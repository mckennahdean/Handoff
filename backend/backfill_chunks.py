"""One-time backfill: create retrieval chunks for procedures that
were approved before chunked retrieval existed.

Safe to rerun: procedures that already have chunks are skipped.

Run from the repo root:
    python -m backend.backfill_chunks
"""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import engine
from backend.db_service import (
    procedure_chunk_texts,
    replace_procedure_chunks
)
from backend.gemini_service import embed_texts
from backend.models import Procedure, ProcedureChunk


if __name__ == "__main__":
    with Session(engine) as session:
        already_chunked = set(session.scalars(
            select(ProcedureChunk.procedure_id).distinct()
        ))

        procedures = session.scalars(
            select(Procedure)
            .where(Procedure.status == "approved")
            .order_by(Procedure.id)
        ).all()

        for procedure in procedures:
            if procedure.id in already_chunked:
                print(f"Skipped {procedure.title} (already chunked)")
                continue

            texts = procedure_chunk_texts({
                "title": procedure.title,
                "steps": json.loads(procedure.steps),
                "warnings": json.loads(procedure.warnings)
            })
            vectors = embed_texts(texts)

            replace_procedure_chunks(session, procedure.id, texts, vectors)

            # Commit each procedure, so progress survives a failure.
            session.commit()
            print(f"Chunked {procedure.title}: {len(texts)} chunks")

    print("Backfill complete.")