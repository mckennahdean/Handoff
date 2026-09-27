"""Load the Maple & Main Coffee demo procedures into Handoff.

A fresh install has no procedures, so there is nothing to ask
about until the owner records some. This approves the seven demo
procedures so a new install can try Ask Handoff right away.

Safe to rerun: a procedure whose title already exists is skipped.
The first run uses about 95 embedding requests.

Run from the repo root:
    python -m backend.seed_demo
In Docker:
    docker compose exec backend python -m backend.seed_demo
"""
import json
import time
from pathlib import Path

from backend import db_service

DEMO_FILE = Path(__file__).parent / "demo_procedures.json"

# Every text in a batch counts toward the free tier's limit of 100
# embedding requests per minute, so pause between procedures.
SECONDS_BETWEEN_PROCEDURES = 15


def seed(pause_seconds: float = SECONDS_BETWEEN_PROCEDURES) -> int:
    """Approve each demo procedure that does not exist yet.
    Returns the number of procedures added."""
    with open(DEMO_FILE, encoding="utf-8") as file:
        demo_procedures = json.load(file)

    existing_titles = {
        procedure["title"] for procedure in db_service.get_procedures()
    }

    added = 0

    for procedure_data in demo_procedures:
        if procedure_data["title"] in existing_titles:
            print(f"Skipped {procedure_data['title']} (already exists)")
            continue

        if added:
            time.sleep(pause_seconds)

        db_service.save_procedure(procedure_data)
        added += 1
        print(f"Added {procedure_data['title']}")

    return added


if __name__ == "__main__":
    count = seed()
    print(f"Seeding complete: {count} procedure(s) added.")