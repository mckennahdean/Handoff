from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from backend.db_service import (
    get_procedures,
    save_procedure,
    find_best_matching_procedure,
    log_gap,
    get_gaps
)

from backend.gemini_service import (
    structure_procedure,
    answer_question_from_procedure
)


app = FastAPI()


class QueryRequest(BaseModel):
    question: str


class ProcedureRequest(BaseModel):
    text: str


class ProcedureResponse(BaseModel):
    title: str
    steps: List[str]
    warnings: List[str]


class ApprovedProcedure(BaseModel):
    title: str
    steps: List[str]
    warnings: List[str]


@app.get("/")
def home():
    return {
        "message": "Handoff backend is running"
    }


@app.post(
    "/api/structure-procedure",
    response_model=ProcedureResponse
)
def create_structure(
    request: ProcedureRequest
):
    result = structure_procedure(
        request.text
    )

    return result


@app.get("/api/procedures")
def list_procedures():
    return get_procedures()


@app.get("/api/gaps")
def list_gaps():
    return get_gaps()


@app.post("/api/approve-procedure")
def approve_procedure(
    procedure: ApprovedProcedure
):
    saved = save_procedure(
        procedure.model_dump()
    )

    return {
        "status": "approved",
        "procedure_id": saved.id,
        "title": saved.title,
        "last_confirmed": saved.last_confirmed
    }


@app.post("/api/query")
def query_procedure(
    request: QueryRequest
):
    procedure, similarity = (
        find_best_matching_procedure(
            request.question
        )
    )

    if procedure is None:
        log_gap(
            request.question,
            0.0
        )

        return {
            "status": "not_documented",
            "message": (
                "No matching procedure was found."
            ),
            "gap_logged": True
        }

    threshold = 0.70

    if similarity < threshold:
        log_gap(
            request.question,
            similarity
        )

        return {
            "status": "not_documented",
            "message": (
                "This information is not currently documented."
            ),
            "similarity": similarity,
            "gap_logged": True
        }

    answer = answer_question_from_procedure(
        request.question,
        procedure
    )

    return {
        "status": "answered",
        "answer": answer,
        "source_procedure": procedure.title,
        "procedure_id": procedure.id,
        "similarity": similarity,
        "last_confirmed": procedure.last_confirmed
    }