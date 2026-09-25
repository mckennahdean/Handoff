"""Knowledge gap grouping evaluation for Handoff.

Checks whether GAP_GROUPING_THRESHOLD groups same-meaning questions
and keeps different questions apart. Embeds questions exactly the
way log_gap() does (no task type) and shares the retrieval
harness's cache, so reruns are free.

Run from the repo root:
    python -m evaluation.run_grouping
"""
import json
from datetime import datetime, timezone

from backend.config import GAP_GROUPING_THRESHOLD
from evaluation.run_retrieval import (
    CACHE_FILE,
    EMBEDDING_MODEL,
    EVAL_DIR,
    QUESTIONS_FILE,
    EmbeddingCache,
    dot,
    load_json,
    unit,
)

RESULTS_FILE = EVAL_DIR / "results" / "grouping_results.json"

# 0.60, 0.61, ... 0.95
THRESHOLDS = [round(0.60 + 0.01 * i, 2) for i in range(36)]


def sweep(rows):
    results = []

    for threshold in THRESHOLDS:
        correct = sum(
            1 for r in rows
            if (r["similarity"] >= threshold) == r["same"]
        )
        false_merges = sum(
            1 for r in rows
            if not r["same"] and r["similarity"] >= threshold
        )
        missed_groups = sum(
            1 for r in rows
            if r["same"] and r["similarity"] < threshold
        )

        results.append({
            "threshold": threshold,
            "accuracy": round(correct / len(rows), 4),
            "false_merges": false_merges,
            "missed_groups": missed_groups,
        })

    return results


def pick_threshold(sweep_rows):
    # Middle of the best-scoring range, for margin on both sides.
    best = max(r["accuracy"] for r in sweep_rows)
    tied = [r for r in sweep_rows if r["accuracy"] == best]
    return tied[len(tied) // 2]


def main():
    pairs = load_json(QUESTIONS_FILE)["pairs"]
    cache = EmbeddingCache(CACHE_FILE)
    rows = []

    try:
        for pair in pairs:
            a = unit(cache.embed(pair["a"]))
            b = unit(cache.embed(pair["b"]))

            rows.append({
                "id": pair["id"],
                "kind": pair["kind"],
                "same": pair["same"],
                "a": pair["a"],
                "b": pair["b"],
                "similarity": round(dot(a, b), 4),
            })
    finally:
        cache.save()
        print(f"New embedding requests this run: {cache.new_requests}")

    sweep_rows = sweep(rows)
    best = pick_threshold(sweep_rows)
    current = next(
        r for r in sweep_rows
        if r["threshold"] == round(GAP_GROUPING_THRESHOLD, 2)
    )

    print("\n=== Score range by kind ===")
    for kind in ["paraphrase", "hard_negative", "unrelated"]:
        scores = [r["similarity"] for r in rows if r["kind"] == kind]
        print(
            f"{kind:<15} n={len(scores):<3}"
            f" min={min(scores):.3f}  max={max(scores):.3f}"
        )

    print(
        f"\nCurrent threshold {GAP_GROUPING_THRESHOLD:.2f}: "
        f"accuracy {current['accuracy']:.0%}, "
        f"false merges {current['false_merges']}, "
        f"missed groups {current['missed_groups']}"
    )
    print(
        f"Best threshold {best['threshold']:.2f}: "
        f"accuracy {best['accuracy']:.0%}, "
        f"false merges {best['false_merges']}, "
        f"missed groups {best['missed_groups']}"
    )

    print(
        f"\n=== All pairs, highest similarity first "
        f"(X = wrong at {GAP_GROUPING_THRESHOLD:.2f}) ==="
    )
    for r in sorted(rows, key=lambda r: r["similarity"], reverse=True):
        grouped = r["similarity"] >= GAP_GROUPING_THRESHOLD
        mark = "  " if grouped == r["same"] else "X "
        label = "same" if r["same"] else "diff"
        print(
            f"{mark}{r['id']}  {r['similarity']:.3f}  {label}  "
            f"{r['kind']:<14} {r['a']}  |  {r['b']}"
        )

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump({
            "run_at": datetime.now(timezone.utc).isoformat(),
            "embedding_model": EMBEDDING_MODEL,
            "current_threshold": GAP_GROUPING_THRESHOLD,
            "best": best,
            "sweep": sweep_rows,
            "pairs": rows,
        }, file, indent=2)

    print(f"\nFull results written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()