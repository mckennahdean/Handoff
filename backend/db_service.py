import json
import os

from dotenv import load_dotenv
from google import genai

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import engine
from backend.models import Procedure, Gap

from datetime import datetime, timezone
from typing import Optional


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def create_embedding(procedure_data: dict) -> list:
    text_for_embedding = (
        procedure_data["title"]
        + " "
        + " ".join(procedure_data["steps"])
        + " "
        + " ".join(procedure_data["warnings"])
    )

    embedding_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text_for_embedding
    )

    return embedding_response.embeddings[0].values


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
    """Approve a procedure: embed it and mark it approved.

    With a procedure_id, approves that draft, or re-approves an
    edited procedure and increments its version. Without one,
    creates and approves a new procedure in one step.
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

        procedure.title = procedure_data["title"]
        procedure.steps = json.dumps(procedure_data["steps"])
        procedure.warnings = json.dumps(procedure_data["warnings"])
        procedure.embedding = create_embedding(procedure_data)
        procedure.status = "approved"
        procedure.last_confirmed = datetime.now(timezone.utc)

        session.commit()
        session.refresh(procedure)

        return procedure


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
    embedding_response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question
    )

    question_embedding = (
        embedding_response.embeddings[0].values
    )

    with Session(engine) as session:
        distance = Procedure.embedding.cosine_distance(
            question_embedding
        )

        result = session.execute(
            select(
                Procedure,
                distance.label("distance")
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


def log_gap(question: str, similarity: float):
    with Session(engine) as session:
        gap = Gap(
            question=question,
            similarity=str(similarity)
        )

        session.add(gap)
        session.commit()
        session.refresh(gap)

        return gap


def get_gaps():
    with Session(engine) as session:
        gaps = session.query(Gap).all()

        return [
            {
                "id": gap.id,
                "question": gap.question,
                "similarity": gap.similarity
            }
            for gap in gaps
        ]