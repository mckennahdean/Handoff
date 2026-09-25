import os

from dotenv import load_dotenv


load_dotenv()

# Minimum cosine similarity for Handoff to answer from a procedure.
# Below this, Handoff abstains and logs a knowledge gap.
# 0.68 was chosen from the evaluation (evaluation/run_retrieval.py):
# the midpoint between the highest near-miss (0.670) and the lowest
# correctly retrieved question (0.691), using chunked retrieval.
ANSWER_THRESHOLD = float(os.getenv("ANSWER_THRESHOLD", "0.68"))

# Minimum similarity for two unanswered questions to count as the
# same knowledge gap. Stricter than the answer threshold, because
# two questions must mean nearly the same thing to be grouped.
GAP_GROUPING_THRESHOLD = float(os.getenv("GAP_GROUPING_THRESHOLD", "0.75"))