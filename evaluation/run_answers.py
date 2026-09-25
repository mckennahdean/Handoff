"""Answer quality, Generation Gate, and latency evaluation.

1. Real pipeline: each answerable question goes through the same
   steps as /api/query (embed, chunk retrieval, Threshold Gate,
   answer, Generation Gate) using the app's own functions.
2. Generation Gate alone: each should-abstain question is sent to
   the AI with its closest procedure even when the Threshold Gate
   would have stopped it, to test the second gate by itself.
3. Latency: live timings for question embedding and answering.

Never touches the database. Paced under the free tier's 15 text
requests per minute (about 42 text and 43 embedding requests).
Progress is saved after every question, so an interrupted run
resumes where it stopped.

Run from the repo root:
    python -m evaluation.run_answers
"""
import json
import statistics
import time
from datetime import datetime, timezone
from types import SimpleNamespace

from google.genai import errors

from backend.config import ANSWER_THRESHOLD
from backend.db_service import procedure_chunk_texts
from backend.gemini_service import (
    NOT_DOCUMENTED_REPLY,
    TEXT_MODEL,
    answer_question_from_procedure,
    embed_text,
)
from evaluation.run_retrieval import (
    CACHE_FILE,
    EVAL_DIR,
    PROCEDURES_FILE,
    QUESTIONS_FILE,
    EmbeddingCache,
    dot,
    load_json,
    unit,
)

RESULTS_FILE = EVAL_DIR / "results" / "answer_results.json"

# Lives in the gitignored cache folder; deleted after a full run.
PROGRESS_FILE = EVAL_DIR / "cache" / "answer_progress.json"

# 60 seconds / 15 requests = 4 seconds; 4.5 leaves headroom.
SECONDS_BETWEEN_TEXT_REQUESTS = 4.5


def timed(call, *args):
    """Run an API call and return (result, seconds).

    The app's own retry already handles brief 5xx errors. If those
    retries run out, wait 30 seconds and try again; on a quota error
    (429), wait 60 seconds. Waits are never counted as latency.
    """
    for attempt in range(4):
        try:
            start = time.perf_counter()
            result = call(*args)
            return result, time.perf_counter() - start

        except errors.APIError as error:
            if error.code == 429:
                wait = 60
            elif error.code >= 500:
                wait = 30
            else:
                raise

            print(f"  API error {error.code}; waiting {wait}s...")
            time.sleep(wait)

    raise RuntimeError(
        "The API kept failing. Progress is saved; rerun to resume."
    )


def as_db_procedure(procedure):
    """Shape a procedures.json entry like a database row, where
    steps and warnings are stored as JSON text."""
    return SimpleNamespace(
        id=procedure["id"],
        title=procedure["title"],
        steps=json.dumps(procedure["steps"]),
        warnings=json.dumps(procedure["warnings"]),
    )


def build_chunk_index(procedures, cache):
    # Same chunks the app stores; all already cached, so free.
    return [
        (procedure["id"], unit(cache.embed(text)))
        for procedure in procedures
        for text in procedure_chunk_texts(procedure)
    ]


def best_procedure(question_vector, index):
    best_id, best_score = None, -1.0

    for procedure_id, vector in index:
        score = dot(question_vector, vector)
        if score > best_score:
            best_id, best_score = procedure_id, score

    return best_id, best_score


def evaluate_question(question, index, by_id):
    vector, embed_seconds = timed(embed_text, question["question"])
    procedure_id, score = best_procedure(unit(vector), index)
    passes_threshold = score >= ANSWER_THRESHOLD

    # Answerable questions follow the real pipeline, so they only
    # reach the AI if they pass the Threshold Gate. Should-abstain
    # questions always reach it, to test the Generation Gate alone.
    answer, generate_seconds = None, None

    if passes_threshold or not question["expected"]:
        time.sleep(SECONDS_BETWEEN_TEXT_REQUESTS)
        answer, generate_seconds = timed(
            answer_question_from_procedure,
            question["question"],
            as_db_procedure(by_id[procedure_id]),
        )

    # The same check /api/query uses for the Generation Gate.
    refused = (
        answer is not None
        and NOT_DOCUMENTED_REPLY.lower() in answer.lower()
    )

    if not passes_threshold:
        outcome = "blocked_by_threshold_gate"
    elif refused:
        outcome = "refused_by_generation_gate"
    else:
        outcome = "answered"

    return {
        "id": question["id"],
        "type": question["type"],
        "question": question["question"],
        "expected": question["expected"],
        "key_fact": question.get("key_fact"),
        "procedure_id": procedure_id,
        "score": round(score, 4),
        "passes_threshold": passes_threshold,
        "answer": answer,
        "refused": refused,
        "outcome": outcome,
        "embed_seconds": round(embed_seconds, 3),
        "generate_seconds": (
            round(generate_seconds, 3) if generate_seconds else None
        ),
    }


def save_progress(settings, done):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump({"settings": settings, "rows": done}, file)


def describe(values):
    if not values:
        return "no samples"

    return (
        f"median {statistics.median(values):.2f}s, "
        f"worst {max(values):.2f}s (n={len(values)})"
    )


def print_report(rows):
    answerable = [r for r in rows if r["expected"]]
    unanswerable = [r for r in rows if not r["expected"]]

    print("\n=== 1. Answerable questions: real pipeline ===")
    for r in answerable:
        right = "right" if r["procedure_id"] in r["expected"] else "WRONG"
        print(
            f"\n{r['id']} [{r['outcome']}] procedure {r['procedure_id']} "
            f"({right}), score {r['score']:.3f}"
        )
        print(f"  Q: {r['question']}")
        print(f"  Key fact: {r['key_fact']}")
        if r["answer"]:
            print(f"  A: {r['answer']}")

    print("\n=== 2. Should-abstain questions ===")
    for r in unanswerable:
        if not r["passes_threshold"]:
            real = "stopped by Threshold Gate"
        elif r["refused"]:
            real = "stopped by Generation Gate"
        else:
            real = "NOT STOPPED"

        alone = "refused" if r["refused"] else "ANSWERED"
        print(
            f"{r['id']} score {r['score']:.3f}, procedure "
            f"{r['procedure_id']}: {real}; Generation Gate alone: {alone}"
        )
        if not r["refused"]:
            print(f"  A: {r['answer']}")

    answered = [r for r in answerable if r["outcome"] == "answered"]
    real_abstained = [r for r in unanswerable if r["outcome"] != "answered"]
    gate_alone = [r for r in unanswerable if r["refused"]]

    print("\n=== Summary ===")
    print(f"Answerable answered: {len(answered)}/{len(answerable)}")
    print(
        f"Should-abstain abstained (real pipeline): "
        f"{len(real_abstained)}/{len(unanswerable)}"
    )
    print(
        f"Generation Gate alone caught: "
        f"{len(gate_alone)}/{len(unanswerable)}"
    )

    print("\n=== Latency ===")
    print("Question embedding: " + describe(
        [r["embed_seconds"] for r in rows]
    ))
    print("Answer generation:  " + describe(
        [r["generate_seconds"] for r in rows if r["generate_seconds"]]
    ))
    print("Answered end to end (embed + generate): " + describe(
        [r["embed_seconds"] + r["generate_seconds"] for r in answered]
    ))


def main():
    procedures = load_json(PROCEDURES_FILE)
    by_id = {p["id"]: p for p in procedures}
    questions = load_json(QUESTIONS_FILE)["questions"]

    cache = EmbeddingCache(CACHE_FILE)
    index = build_chunk_index(procedures, cache)
    cache.save()

    # Saved progress is reused only if nothing it depends on changed.
    settings = {
        "text_model": TEXT_MODEL,
        "answer_threshold": ANSWER_THRESHOLD,
        "procedure_versions": {
            str(p["id"]): p["version"] for p in procedures
        },
    }

    done = {}
    if PROGRESS_FILE.exists():
        saved = load_json(PROGRESS_FILE)
        if saved.get("settings") == settings:
            done = saved["rows"]
            print(f"Resuming: {len(done)} questions already done.")
        else:
            print("Settings changed since the last run; starting fresh.")

    remaining = len(questions) - len(done)
    print(
        f"Running {remaining} questions with {TEXT_MODEL} "
        f"at threshold {ANSWER_THRESHOLD:.2f} "
        f"(about {remaining * 6.5 / 60:.0f} minutes)."
    )

    if remaining:
        # Warm up the client so setup time is not counted as latency.
        timed(embed_text, "warm up")

    rows = []

    for number, question in enumerate(questions, start=1):
        if question["id"] in done:
            rows.append(done[question["id"]])
            continue

        row = evaluate_question(question, index, by_id)
        rows.append(row)
        done[question["id"]] = row
        save_progress(settings, done)

        print(f"  [{number}/{len(questions)}] {row['id']} {row['outcome']}")

    print_report(rows)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump({
            "run_at": datetime.now(timezone.utc).isoformat(),
            **settings,
            "questions": rows,
        }, file, indent=2)

    # The full run is recorded in the results file; progress is done.
    PROGRESS_FILE.unlink(missing_ok=True)

    print(f"\nFull results written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()