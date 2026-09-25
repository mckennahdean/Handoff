import json
import os

from dotenv import load_dotenv

from sqlalchemy.orm import Session
from sqlalchemy import case, delete, select

from backend.database import engine
from backend.models import Procedure, ProcedureChunk, Gap
from backend.config import ANSWER_THRESHOLD, GAP_GROUPING_THRESHOLD
from backend.gemini_service import embed_text, embed_texts

from datetime import datetime, timezone
from typing import Optional


load_dotenv()

def procedure_chunk_texts(procedure_data: dict) -> list:
    """Split a procedure into one retrieval chunk per step and warning.

    Each chunk carries the title, so a short step still says which
    procedure it belongs to. Embedding whole procedures diluted
    their meaning; chunking raised retrieval from 26/28 to 28/28
    in the evaluation (Strategy C in evaluation/run_retrieval.py).
    """
    title = procedure_data["title"]

    return [
        f"{title}: {item}"
        for item in procedure_data["steps"] + procedure_data["warnings"]
    ]


def replace_procedure_chunks(
    session,
    procedure_id: int,
    texts: list,
    vectors: list
):
    """Swap a procedure's retrieval chunks for a fresh set."""
    session.execute(
        delete(ProcedureChunk).where(
            ProcedureChunk.procedure_id == procedure_id
        )
    )

    session.add_all([
        ProcedureChunk(
            procedure_id=procedure_id,
            text=text,
            embedding=vector
        )
        for text, vector in zip(texts, vectors)
    ])


def save_draft(procedure_data: dict):
    """Store an AI-structured procedure awaiting owner approval.

    Drafts have no embedding, so retrieval can never return them.
    """
    with Session(engine) as session:
        procedure = Procedure(
            title=procedure_data["title"],
            steps=json.dumps(procedure_data["steps"]),
            warnings=json.dumps(procedure_data["warnings"]),
            capture_method=procedure_data.get("capture_method"),
            gap_questions=json.dumps(
                procedure_data.get("gap_questions", [])
            ),
            status="pending"
        )

        session.add(procedure)
        session.commit()
        session.refresh(procedure)

        return procedure


def save_procedure(
    procedure_data: dict,
    procedure_id: Optional[int] = None
):
    """Approve a procedure: chunk and embed it, and mark it approved.

    With a procedure_id, approves that draft, or re-approves an
    edited procedure and increments its version. Without one,
    creates and approves a new procedure in one step.
    Also resolves any open knowledge gaps the procedure now answers.
    Returns None if the procedure_id does not exist.
    """
    with Session(engine) as session:
        if procedure_id is None:
            procedure = Procedure()
            session.add(procedure)

        else:
            procedure = session.get(Procedure, procedure_id)

            if procedure is None:
                return None

            if procedure.status == "approved":
                procedure.version += 1

        # Embed before changing anything else. If the AI service
        # fails, the session closes without a commit and nothing
        # is saved, so approval stays all-or-nothing.
        chunk_texts = procedure_chunk_texts(procedure_data)
        chunk_vectors = embed_texts(chunk_texts)

        procedure.title = procedure_data["title"]
        procedure.steps = json.dumps(procedure_data["steps"])
        procedure.warnings = json.dumps(procedure_data["warnings"])
        # Retired: retrieval now uses procedure_chunks. The column
        # stays so older rows remain valid without a migration.
        procedure.embedding = None
        procedure.status = "approved"
        procedure.last_confirmed = datetime.now(timezone.utc)

        # Gives a brand-new procedure its id before chunks and
        # gaps link to it.
        session.flush()

        replace_procedure_chunks(
            session,
            procedure.id,
            chunk_texts,
            chunk_vectors
        )
        session.flush()

        resolved_count = _resolve_gaps_covered_by(session, procedure)

        session.commit()
        session.refresh(procedure)

        procedure.resolved_gap_count = resolved_count

        return procedure


def _resolve_gaps_covered_by(session, procedure) -> int:
    """Close open knowledge gaps that this procedure now answers.

    Uses the same test as retrieval: a gap is resolved when its
    question matches one of this procedure's chunks at or above
    the answer threshold.
    """
    matching_chunk = (
        select(ProcedureChunk.id)
        .where(
            ProcedureChunk.procedure_id == procedure.id,
            ProcedureChunk.embedding.cosine_distance(Gap.embedding)
            <= 1 - ANSWER_THRESHOLD
        )
        .exists()
    )

    covered_gaps = session.scalars(
        select(Gap).where(
            Gap.status == "open",
            Gap.embedding.is_not(None),
            matching_chunk
        )
    ).all()

    now = datetime.now(timezone.utc)

    for gap in covered_gaps:
        gap.status = "resolved"
        gap.resolved_at = now
        gap.resolved_by_procedure_id = procedure.id

    return len(covered_gaps)


def get_procedure(procedure_id: int):
    with Session(engine) as session:
        return session.get(Procedure, procedure_id)


def procedure_to_dict(procedure) -> dict:
    return {
        "id": procedure.id,
        "title": procedure.title,
        "steps": json.loads(procedure.steps),
        "warnings": json.loads(procedure.warnings),
        "status": procedure.status,
        "version": procedure.version,
        "capture_method": procedure.capture_method,
        "gap_questions": (
            json.loads(procedure.gap_questions)
            if procedure.gap_questions
            else []
        ),
        "last_confirmed": (
            procedure.last_confirmed
            if procedure.status == "approved"
            else None
        )
    }


def get_procedures(include_pending: bool = True):
    with Session(engine) as session:
        query = select(Procedure).order_by(
            Procedure.last_confirmed.desc()
        )

        if not include_pending:
            query = query.where(Procedure.status == "approved")

        procedures = session.scalars(query).all()

        return [
            {
                "id": procedure.id,
                "title": procedure.title,
                "status": procedure.status,
                "version": procedure.version,
                "last_confirmed": (
                    procedure.last_confirmed
                    if procedure.status == "approved"
                    else None
                )
            }
            for procedure in procedures
        ]


def find_best_matching_procedure(question: str):
    """Return the approved procedure containing the chunk closest
    to the question, and that chunk's similarity."""
    question_embedding = embed_text(question)

    with Session(engine) as session:
        distance = ProcedureChunk.embedding.cosine_distance(
            question_embedding
        )

        result = session.execute(
            select(
                Procedure,
                distance.label("distance")
            )
            .join(
                ProcedureChunk,
                ProcedureChunk.procedure_id == Procedure.id
            )
            .where(
                Procedure.status == "approved"
            )
            .order_by(distance)
            .limit(1)
        ).first()

        if result is None:
            return None, None

        procedure, distance_value = result

        similarity = 1 - distance_value

        return procedure, similarity

def add_question_variant(
    original: str,
    variants: list,
    question: str
) -> list:
    """Return variants with this wording added, unless it repeats
    the original question or a wording already recorded (ignoring
    case), so the list stays short and meaningful."""
    known = {original.strip().lower()} | {
        variant.strip().lower() for variant in variants
    }

    if question.strip().lower() in known:
        return variants

    return variants + [question.strip()]

def log_gap(question: str, similarity: float):
    """Record an unanswered question, grouping it with an existing
    open gap when the two questions mean the same thing."""
    question_embedding = embed_text(question)
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        distance = Gap.embedding.cosine_distance(question_embedding)

        match = session.execute(
            select(Gap, distance.label("distance"))
            .where(
                Gap.status == "open",
                Gap.embedding.is_not(None)
            )
            .order_by(distance)
            .limit(1)
        ).first()

        if match is not None and 1 - match[1] >= GAP_GROUPING_THRESHOLD:
            gap = match[0]
            gap.frequency_count += 1
            gap.last_asked_at = now

            # Keep this wording too, so a mistaken grouping never
            # hides a different question from the owner.
            gap.variants = json.dumps(add_question_variant(
                gap.question,
                json.loads(gap.variants) if gap.variants else [],
                question
            ))            

            # Track the closest the knowledge base has come.
            gap.similarity = max(gap.similarity or 0.0, float(similarity))

        else:
            gap = Gap(
                question=question,
                similarity=float(similarity),
                embedding=question_embedding,
                status="open",
                created_at=now,
                last_asked_at=now
            )

            session.add(gap)

        session.commit()
        session.refresh(gap)

        return gap


def get_gaps():
    with Session(engine) as session:
        procedure_titles = dict(
            session.execute(
                select(Procedure.id, Procedure.title)
            ).all()
        )

        gaps = session.scalars(
            select(Gap).order_by(
                # Open gaps first, then the most-asked, then the newest.
                case((Gap.status == "open", 0), else_=1),
                Gap.frequency_count.desc(),
                Gap.last_asked_at.desc().nulls_last()
            )
        ).all()

        return [
            {
                "id": gap.id,
                "question": gap.question,
                "similarity": gap.similarity,
                "frequency_count": gap.frequency_count,
                "variants": json.loads(gap.variants) if gap.variants else [],
                "status": gap.status,
                "created_at": gap.created_at,
                "last_asked_at": gap.last_asked_at or gap.created_at,
                "resolved_at": gap.resolved_at,
                "resolved_by_procedure_id": gap.resolved_by_procedure_id,
                "resolved_by_title": procedure_titles.get(
                    gap.resolved_by_procedure_id
                )
            }
            for gap in gaps
        ]


def dismiss_gap(gap_id: int):
    with Session(engine) as session:
        gap = session.get(Gap, gap_id)

        if gap is None:
            return None

        gap.status = "dismissed"
        gap.resolved_at = datetime.now(timezone.utc)
        session.commit()

        return gap_id

def delete_procedure(procedure_id: int):
    """Permanently delete a procedure (approved or draft).
    Knowledge gaps it had resolved reopen, since nothing
    answers them anymore. Returns the number of reopened
    gaps, or None if the procedure does not exist."""
    with Session(engine) as session:
        procedure = session.get(Procedure, procedure_id)

        if procedure is None:
            return None

        reopened = session.scalars(
            select(Gap).where(
                Gap.status == "resolved",
                Gap.resolved_by_procedure_id == procedure_id
            )
        ).all()

        for gap in reopened:
            gap.status = "open"
            gap.resolved_at = None
            gap.resolved_by_procedure_id = None

        session.delete(procedure)
        session.commit()

        return len(reopened)