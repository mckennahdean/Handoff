from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from backend.db_service import save_procedure, get_procedures
from backend.gemini_service import structure_procedure
from backend.db_service import save_procedure

app = FastAPI()


class ProcedureRequest(BaseModel):
    text: str


class ProcedureResponse(BaseModel):
    title: str
    steps: List[str]
    warnings: List[str]


@app.get("/")
def home():
    return {"message": "Handoff backend is running"}


@app.post(
    "/structure-procedure",
    response_model=ProcedureResponse
)
def create_structure(request: ProcedureRequest):
    result = structure_procedure(request.text)

    save_procedure(result)

    return result

@app.get("/procedures")
def list_procedures():
    return get_procedures()