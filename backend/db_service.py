import json
import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Procedure

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def save_procedure(procedure_data: dict):
    text_for_embedding = (
        procedure_data["title"]
        + " "
        + " ".join(procedure_data["steps"])
        + " "
        + " ".join(procedure_data["warnings"])
    )

    embedding_response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text_for_embedding
    )

    embedding = embedding_response.embeddings[0].values

    with Session(engine) as session:
        procedure = Procedure(
            title=procedure_data["title"],
            steps=json.dumps(procedure_data["steps"]),
            warnings=json.dumps(procedure_data["warnings"]),
            embedding=embedding
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
                "title": procedure.title
            }
            for procedure in procedures
        ]
        