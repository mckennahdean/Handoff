import json
import os

from dotenv import load_dotenv
from google import genai

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import engine
from backend.models import Procedure, Gap


load_dotenv()


client = None


def get_client():
    global client

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        client = genai.Client(
            api_key=api_key
        )

    return client


def save_procedure(procedure_data: dict):
    gemini_client = get_client()

    text_for_embedding = (
        procedure_data["title"]
        + " "
        + " ".join(procedure_data["steps"])
        + " "
        + " ".join(procedure_data["warnings"])
    )

    embedding_response = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text_for_embedding
    )

    embedding = embedding_response.embeddings[0].values

    with Session(engine) as session:
        procedure = Procedure(
            title=procedure_data["title"],
            steps=json.dumps(procedure_data["steps"]),
            warnings=json.dumps(procedure_data["warnings"]),
            embedding=embedding,
            status="approved"
        )

        session.add(procedure)
        session.commit()
        session.refresh(procedure)

        return procedure


def get_procedures():
    with Session(engine) as session:
        procedures = session.query(Procedure).all()

        return [
            {
                "id": procedure.id,
                "title": procedure.title,
                "status": procedure.status,
                "last_confirmed": procedure.last_confirmed
            }
            for procedure in procedures
        ]


def find_best_matching_procedure(question: str):
    gemini_client = get_client()

    embedding_response = gemini_client.models.embed_content(
        model="gemini-embedding-2",
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
            similarity=similarity
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
                "similarity": gap.similarity,
                "created_at": gap.created_at
            }
            for gap in gaps
        ]