# Evaluation

This folder measures how well Handoff retrieves, answers, abstains, and groups questions. It runs offline: it reads a snapshot of the procedures from `procedures.json`, computes similarity in Python, and **never touches the Handoff database**. Results are committed in `results/`, so every number in the project README can be traced to a file.

## Test data

- **`procedures.json`**: the 7 approved procedures of Maple & Main Coffee, a fictional coffee shop created for testing. The procedures were written in overlapping pairs (opening vs. closing, the milk fridge vs. the walk-in cooler) so retrieval has to tell similar procedures apart.
- **`questions.json`**:
  - 43 labeled questions: 10 direct, 19 paraphrased (different words than the procedure), 10 near misses (on topic but not documented), and 4 off topic. Each answerable question lists the procedure that answers it and its key fact.
  - 30 labeled question pairs for grouping: 15 paraphrases (same question), 12 hard negatives (same topic, different question), and 3 unrelated.

Question q43 ("What time does the store open?") was found in live testing, not written in advance. It scored 0.670 before the owner added the word "store" to the procedure, and 0.701 after.

## Running it

From the repository root, with the virtual environment active and `GEMINI_API_KEY` set:

```
python -m evaluation.run_retrieval
python -m evaluation.run_grouping
python -m evaluation.run_answers
```

Embeddings are cached in `cache/` (gitignored), so reruns only pay for text that changed. `run_answers` makes about 43 text and 44 embedding requests, paced under the free tier's limits, and resumes where it stopped if interrupted.

To refresh the procedure snapshot from a running database:

```
docker exec handoff-db psql -U handoff_user -d handoff -t -A -c "SELECT json_agg(json_build_object('id', id, 'title', title, 'version', version, 'steps', steps::json, 'warnings', warnings::json) ORDER BY id) FROM procedures WHERE status = 'approved';" | Out-File -Encoding utf8 evaluation\procedures.json
```

(On macOS or Linux, replace the `Out-File` part with `> evaluation/procedures.json`.)

## Results

### Retrieval: four strategies (`run_retrieval.py`)

Each strategy was scored on whether the correct procedure ranks first, and on overall accuracy at a threshold (answerable questions answered plus unanswerable questions refused, out of 43).

| Strategy | Correct procedure first | Accuracy at 0.70 | Best accuracy |
|---|---|---|---|
| A: whole procedure | 27 / 29 | 51% | 81% |
| B: whole procedure, task types | 27 / 29 | 60% | 84% |
| **C: one chunk per step and warning** | **29 / 29** | **91%** | **98%** |
| D: chunks, task types | 29 / 29 | 95% | 95% |

0.70 was the original answer threshold.

**Decision: chunked retrieval (C) at a threshold of 0.68.** Embedding a whole procedure averaged its meaning, so a question about one step scored low. Embedding each step separately lets a question match the exact step that answers it. Under C, no question scores between 0.670 (the highest near miss) and 0.691 (the lowest correct answer); 0.68 sits in the middle of that gap, with room on both sides. The app's live scores matched these offline predictions to within 0.001.

The one question C gets wrong at the threshold is q29, "How often should we descale the espresso machine?" (0.722). It is on topic for Espresso Machine Daily Cleaning, but that procedure never says how often to descale. No threshold can stop it without also blocking real answers, which is why Handoff has a second gate.

### Answers and abstention (`run_answers.py`)

Each question goes through the same steps as the live `/api/query` route: embed, retrieve, Threshold Gate, generate, Generation Gate.

| Measure | Result |
|---|---|
| Answerable questions answered | 29 / 29 |
| Should-abstain questions refused | 14 / 14 (13 by the Threshold Gate, 1 by the Generation Gate) |
| Generation Gate alone, tested on all 14 | 14 / 14 refused |
| Answer quality (graded by hand against key facts) | 28 fully correct, 1 partial, 0 invented facts |

The partial answer (q16) began with "Yes." to a question whose true answer was conditional.

| Latency | Run 1 (weekday midday) | Run 2 (weekend evening) |
|---|---|---|
| Median, question to answer | 3.6 s | 1.3 s |
| Slowest answer | 33 s | 4.3 s |

The same code produced very different times, because response time depends on the AI provider's load on the free tier.

### Grouping knowledge gaps (`run_grouping.py`)

| Pair type | Similarity range |
|---|---|
| Paraphrases (should group) | 0.734 to 0.938 |
| Hard negatives (should not group) | 0.578 to 0.807 |
| Unrelated | 0.492 to 0.591 |

The paraphrase and hard-negative ranges overlap, so no threshold separates them: embeddings measure topic, not the specific question asked. At 0.75, accuracy is 83% (3 false merges, 2 missed groups). 0.73 scores 90% on these pairs, but it sits 0.002 above one hard negative and 0.004 below one paraphrase, so it is fitted to this particular set and was not adopted.

**Decision: keep 0.75, and fix the problem in the design instead.** Every wording is stored with its gap ("Also Asked As"), so a wrong grouping never hides a question from the owner.

## Limitations of this evaluation

- The data set is small and synthetic: one fictional business, 43 questions, and 30 pairs, written and labeled by the project team.
- Answer quality was graded by hand by the team.
- Latency was measured on the Gemini free tier, where provider load varies widely.
- Auto-resolve (resolving a gap when a procedure is approved) uses the Threshold Gate only. Among the 14 should-abstain questions, one (q29, descale) would be marked resolved if Espresso Machine Daily Cleaning were re-approved.