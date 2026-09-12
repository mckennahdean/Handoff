import os
import shutil
import tempfile

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)
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
    answer_question_from_procedure,
    transcribe_audio
)


app = FastAPI()


# Audio upload settings
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".webm"
}

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB


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


@app.post("/api/upload-audio")
def upload_audio(
    audio_file: UploadFile = File(...)
):
    # Make sure a filename exists
    if not audio_file.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio file is required."
        )

    file_extension = os.path.splitext(
        audio_file.filename
    )[1].lower()

    # Check supported audio format
    if file_extension not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio file format."
        )

    temp_file_path = None

    try:
        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp_file:

            shutil.copyfileobj(
                audio_file.file,
                temp_file
            )

            temp_file_path = temp_file.name

        # Check if file is empty
        file_size = os.path.getsize(
            temp_file_path
        )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Audio file cannot be empty."
            )

        # Check file size
        if file_size > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Audio file exceeds the 10 MB limit."
            )

        # Send audio to Gemini
        try:
            transcript = transcribe_audio(
                temp_file_path
            )

        except Exception as error:
            print(
                "Transcription error:",
                error
            )

            raise HTTPException(
                status_code=500,
                detail="Transcription service error."
            )

        # Make sure Gemini returned text
        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=500,
                detail="Transcription service returned an empty transcript."
            )

        return {
            "transcript": transcript.strip()
        }

    finally:
        # Remove temporary file
        if (
            temp_file_path
            and os.path.exists(temp_file_path)
        ):
            os.remove(temp_file_path)


@app.post(
    "/api/structure-procedure",
    response_model=ProcedureResponse
)
def create_structure(
    request: ProcedureRequest
):
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Transcript text cannot be empty."
        )

    try:
        result = structure_procedure(
            request.text
        )

        return result

    except Exception as error:
        print(
            "Procedure structuring error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="LLM service error."
        )


@app.get("/api/procedures")
def list_procedures():
    try:
        return get_procedures()

    except Exception as error:
        print(
            "Database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database error."
        )


@app.get("/api/gaps")
def list_gaps():
    try:
        return get_gaps()

    except Exception as error:
        print(
            "Gap database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database error."
        )


@app.post("/api/approve-procedure")
def approve_procedure(
    procedure: ApprovedProcedure
):
    if not procedure.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Procedure title cannot be empty."
        )

    if not procedure.steps:
        raise HTTPException(
            status_code=400,
            detail="Procedure must contain at least one step."
        )

    try:
        saved = save_procedure(
            procedure.model_dump()
        )

        return {
            "status": "approved",
            "procedure_id": saved.id,
            "title": saved.title,
            "last_confirmed": saved.last_confirmed
        }

    except Exception as error:
        print(
            "Procedure approval error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database or embedding service error."
        )


@app.post("/api/query")
def query_procedure(
    request: QueryRequest
):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        procedure, similarity = (
            find_best_matching_procedure(
                request.question
            )
        )

    except Exception as error:
        print(
            "Retrieval error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Embedding or retrieval service error."
        )

    if procedure is None:
        try:
            log_gap(
                request.question,
                0.0
            )

        except Exception as error:
            print(
                "Gap logging error:",
                error
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
        try:
            log_gap(
                request.question,
                similarity
            )

        except Exception as error:
            print(
                "Gap logging error:",
                error
            )

        return {
            "status": "not_documented",
            "message": (
                "This information is not currently documented."
            ),
            "similarity": similarity,
            "gap_logged": True
        }

    try:
        answer = answer_question_from_procedure(
            request.question,
            procedure
        )

    except Exception as error:
        print(
            "Answer generation error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="LLM service error."
        )

    return {
        "status": "answered",
        "answer": answer,
        "source_procedure": procedure.title,
        "procedure_id": procedure.id,
        "similarity": similarity,
        "last_confirmed": procedure.last_confirmed
    }