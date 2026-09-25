"""Retrieval and abstention evaluation for Handoff.

Compares four embedding strategies against the labeled Maple & Main
questions. Similarity is computed in Python, so this never touches
the Handoff database. Every embedding is cached on disk, so only the
first run spends API quota; reruns are free.

Run from the repo root:
    python -m evaluation.run_retrieval
"""
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from google.genai import errors, types

from backend.gemini_service import EMBEDDING_MODEL, get_client

EVAL_DIR = Path(__file__).parent
PROCEDURES_FILE = EVAL_DIR / "procedures.json"
QUESTIONS_FILE = EVAL_DIR / "questions.json"
CACHE_FILE = EVAL_DIR / "cache" / "embeddings.json"
RESULTS_FILE = EVAL_DIR / "results" / "retrieval_results.json"

# The app's current Threshold Gate, for comparison.
CURRENT_THRESHOLD = 0.70

# Stay under the free tier's 100 embedding requests per minute.
SECONDS_BETWEEN_REQUESTS = 0.7

STRATEGIES = {
    "A_whole_no_task": {"chunks": False, "tasks": False},
    "B_whole_task_types": {"chunks": False, "tasks": True},
    "C_chunks_no_task": {"chunks": True, "tasks": False},
    "D_chunks_task_types": {"chunks": True, "tasks": True},
}

# 0.50, 0.51, ... 0.90
THRESHOLDS = [round(0.50 + 0.01 * i, 2) for i in range(41)]


def load_json(path):
    # utf-8-sig also accepts files that start with a BOM marker.
    with open(path, encoding="utf-8-sig") as file:
        return json.load(file)


class EmbeddingCache:
    """Embeds text through Gemini, remembering every result on disk."""

    def __init__(self, path):
        self.path = path
        self.data = load_json(path) if path.exists() else {}
        self.new_requests = 0

    def embed(self, text, task_type=None):
        key = hashlib.sha256(
            f"{EMBEDDING_MODEL}|{task_type}|{text}".encode("utf-8")
        ).hexdigest()

        if key not in self.data:
            self.data[key] = self._request(text, task_type)
            self.new_requests += 1

            if self.new_requests % 20 == 0:
                print(f"  {self.new_requests} new embeddings so far...")
                self.save()

        return self.data[key]

    def _request(self, text, task_type):
        config = (
            types.EmbedContentConfig(task_type=task_type)
            if task_type else None
        )

        for attempt in range(5):
            try:
                time.sleep(SECONDS_BETWEEN_REQUESTS)
                response = get_client().models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text,
                    config=config
                )
                return response.embeddings[0].values

            except errors.APIError as error:
                if error.code == 429 or error.code >= 500:
                    wait = 60 if error.code == 429 else 2 ** attempt
                    print(f"  API error {error.code}; waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError("Embedding kept failing. Try again later.")

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file)


def whole_text(procedure):
    # Mirrors create_embedding() in backend/db_service.py.
    return (
        procedure["title"] + " "
        + " ".join(procedure["steps"]) + " "
        + " ".join(procedure["warnings"])
    )


def chunk_texts(procedure):
    # One chunk per step or warning, with the title for context.
    return [
        f"{procedure['title']}: {item}"
        for item in procedure["steps"] + procedure["warnings"]
    ]


def unit(vector):
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def score_questions(procedures, questions, cache, use_chunks, use_tasks):
    doc_task = "RETRIEVAL_DOCUMENT" if use_tasks else None
    query_task = "RETRIEVAL_QUERY" if use_tasks else None

    procedure_vectors = {}

    for procedure in procedures:
        texts = (
            chunk_texts(procedure) if use_chunks
            else [whole_text(procedure)]
        )
        procedure_vectors[procedure["id"]] = [
            unit(cache.embed(text, doc_task)) for text in texts
        ]

    rows = []

    for question in questions:
        question_vector = unit(cache.embed(question["question"], query_task))

        # A procedure's score is its best-matching piece.
        scores = {
            procedure_id: max(dot(question_vector, v) for v in vectors)
            for procedure_id, vectors in procedure_vectors.items()
        }

        top_id = max(scores, key=scores.get)

        rows.append({
            "id": question["id"],
            "type": question["type"],
            "expected": question["expected"],
            "top_procedure": top_id,
            "top_score": round(scores[top_id], 4),
            "correct_procedure": top_id in question["expected"],
        })

    return rows


def sweep(rows):
    answerable = [r for r in rows if r["expected"]]
    unanswerable = [r for r in rows if not r["expected"]]
    results = []

    for threshold in THRESHOLDS:
        answered_right = sum(
            1 for r in answerable
            if r["correct_procedure"] and r["top_score"] >= threshold
        )
        wrong_passed = sum(
            1 for r in answerable
            if not r["correct_procedure"] and r["top_score"] >= threshold
        )
        abstained_right = sum(
            1 for r in unanswerable if r["top_score"] < threshold
        )

        results.append({
            "threshold": threshold,
            "answered_correctly": answered_right,
            "wrong_procedure_passed": wrong_passed,
            "abstained_correctly": abstained_right,
            "overall_accuracy": round(
                (answered_right + abstained_right) / len(rows), 4
            ),
        })

    return results


def pick_threshold(sweep_rows):
    # Among the best-scoring thresholds, take the middle one,
    best = max(r["overall_accuracy"] for r in sweep_rows)
    tied = [r for r in sweep_rows if r["overall_accuracy"] == best]
    return tied[len(tied) // 2]


def summarize(rows, sweep_rows):
    answerable = [r for r in rows if r["expected"]]
    unanswerable = [r for r in rows if not r["expected"]]
    at_current = next(
        r for r in sweep_rows if r["threshold"] == CURRENT_THRESHOLD
    )

    def retrieval_for(question_type):
        group = [r for r in answerable if r["type"] == question_type]
        right = sum(1 for r in group if r["correct_procedure"])
        return f"{right}/{len(group)}"

    return {
        "retrieval_correct": sum(r["correct_procedure"] for r in answerable),
        "answerable_total": len(answerable),
        "retrieval_direct": retrieval_for("direct"),
        "retrieval_paraphrase": retrieval_for("paraphrase"),
        "lowest_correct_answerable_score": min(
            (r["top_score"] for r in answerable if r["correct_procedure"]),
            default=None
        ),
        "highest_unanswerable_score": max(
            r["top_score"] for r in unanswerable
        ),
        "at_current_threshold": at_current,
        "best": pick_threshold(sweep_rows),
    }


def print_report(all_results, questions):
    total = len(questions)

    print("\n=== Summary ===")
    print(
        f"{'Strategy':<22}{'Retrieval':>10}{'Direct':>8}{'Para':>7}"
        f"{'@0.70':>8}{'Best thr':>10}{'Best acc':>10}"
        f"{'Low ans':>9}{'High abs':>10}"
    )

    for name, result in all_results.items():
        s = result["summary"]
        print(
            f"{name:<22}"
            f"{s['retrieval_correct']:>5}/{s['answerable_total']:<4}"
            f"{s['retrieval_direct']:>8}{s['retrieval_paraphrase']:>7}"
            f"{s['at_current_threshold']['overall_accuracy']:>8.0%}"
            f"{s['best']['threshold']:>10.2f}"
            f"{s['best']['overall_accuracy']:>10.0%}"
            f"{s['lowest_correct_answerable_score']:>9.3f}"
            f"{s['highest_unanswerable_score']:>10.3f}"
        )

    print(
        "\nRetrieval = right procedure on top (answerable questions only)."
        "\n@0.70 / Best acc = overall accuracy out of "
        f"{total} (answered correctly + abstained correctly)."
        "\nLow ans = lowest score among correctly retrieved answerable "
        "questions.\nHigh abs = highest score among should-abstain "
        "questions. If Low ans > High abs, a clean threshold exists."
    )

    print("\n=== Per question: top procedure (score), + right / - wrong ===")
    names = list(all_results)
    print(f"{'ID':<5}{'Type':<12}{'Exp':<8}" + "".join(
        f"{name[:1]:>14}" for name in names
    ))

    for index, question in enumerate(questions):
        expected = ",".join(str(e) for e in question["expected"]) or "abstain"
        cells = []

        for name in names:
            row = all_results[name]["questions"][index]
            mark = ""
            if question["expected"]:
                mark = "+" if row["correct_procedure"] else "-"
            cells.append(
                f"{row['top_procedure']}({row['top_score']:.3f}){mark}"
            )

        print(
            f"{question['id']:<5}{question['type']:<12}{expected:<8}"
            + "".join(f"{cell:>14}" for cell in cells)
        )


def main():
    procedures = load_json(PROCEDURES_FILE)
    questions = load_json(QUESTIONS_FILE)["questions"]
    cache = EmbeddingCache(CACHE_FILE)

    print(
        f"Evaluating {len(questions)} questions against "
        f"{len(procedures)} procedures with {EMBEDDING_MODEL}."
    )

    all_results = {}

    try:
        for name, settings in STRATEGIES.items():
            print(f"\nStrategy {name}...")
            rows = score_questions(
                procedures, questions, cache,
                settings["chunks"], settings["tasks"]
            )
            sweep_rows = sweep(rows)
            all_results[name] = {
                "settings": settings,
                "summary": summarize(rows, sweep_rows),
                "sweep": sweep_rows,
                "questions": rows,
            }
    finally:
        # Save even if interrupted, so paid embeddings are never lost.
        cache.save()
        print(f"\nNew embedding requests this run: {cache.new_requests}")

    print_report(all_results, questions)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump({
            "run_at": datetime.now(timezone.utc).isoformat(),
            "embedding_model": EMBEDDING_MODEL,
            "procedure_versions": {
                p["id"]: p["version"] for p in procedures
            },
            "strategies": all_results,
        }, file, indent=2)

    print(f"\nFull results written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()