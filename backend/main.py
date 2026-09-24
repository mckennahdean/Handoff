import os
import shutil
import tempfile


from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from backend.db_service import (
    get_procedures,
    get_procedure,
    procedure_to_dict,
    save_draft,
    save_procedure,
    find_best_matching_procedure,
    log_gap,
    get_gaps
)

from backend.gemini_service import (
    structure_procedure,
    merge_gap_answers,
    MergeAlteredContentError,
    answer_question_from_procedure,
    transcribe_audio
)

from backend.auth_routes import router as auth_router
from backend.auth_service import get_current_user, require_owner
from backend.models import User

app = FastAPI()


# Allow the Vue frontend to communicate with FastAPI during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

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
    gap_questions: List[str] = []


class ApprovedProcedure(BaseModel):
    procedure_id: Optional[int] = None
    title: str
    steps: List[str]
    warnings: List[str]

class DraftProcedure(BaseModel):
    title: str
    steps: List[str]
    warnings: List[str]
    capture_method: Optional[str] = None
    gap_questions: List[str] = []

class GapAnswer(BaseModel):
    question: str
    answer: str


class MergeRequest(BaseModel):
    title: str
    steps: List[str]
    warnings: List[str]
    answers: List[GapAnswer]


@app.get("/")
def home():
    return {
        "message": "Handoff backend is running"
    }


@app.post("/api/upload-audio", dependencies=[Depends(require_owner)])
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
def list_procedures(
    user: User = Depends(get_current_user)
):
    try:
        # Employees only ever see approved procedures.
        return get_procedures(
            include_pending=user.role == "owner"
        )

    except Exception as error:
        print(
            "Database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database error."
        )


@app.get("/api/procedures/{procedure_id}")
def get_procedure_detail(
    procedure_id: int,
    user: User = Depends(get_current_user)
):
    try:
        procedure = get_procedure(procedure_id)

    except Exception as error:
        print(
            "Database error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database error."
        )

    # Employees get 404 for drafts, not 403, so the response
    # does not reveal that an unapproved draft exists.
    if (
        procedure is None
        or (
            procedure.status != "approved"
            and user.role != "owner"
        )
    ):
        raise HTTPException(
            status_code=404,
            detail="Procedure not found."
        )

    return procedure_to_dict(procedure)


@app.post(
    "/api/procedures/drafts",
    status_code=201,
    dependencies=[Depends(require_owner)]
)
def create_draft(draft: DraftProcedure):
    if not draft.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Procedure title cannot be empty."
        )

    try:
        saved = save_draft(draft.model_dump())

    except Exception as error:
        print(
            "Draft save error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database error."
        )

    return {
        "procedure_id": saved.id,
        "status": saved.status
    }

@app.post(
    "/api/procedures/merge-answers",
    dependencies=[Depends(require_owner)]
)
def merge_answers(request: MergeRequest):
    answered = [
        answer.model_dump()
        for answer in request.answers
        if answer.answer.strip()
    ]

    if not answered:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one answer to incorporate."
        )

    try:
        return merge_gap_answers(
            request.title,
            request.steps,
            request.warnings,
            answered
        )

    except MergeAlteredContentError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Handoff's AI tried to change your existing steps, "
                "so the merge was cancelled. Try again, or choose "
                "I'll Add It Myself."
            )
        )

    except Exception as error:
        print(
            "Merge error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="LLM service error."
        )

@app.get("/api/gaps", dependencies=[Depends(require_owner)])
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


@app.post("/api/approve-procedure", dependencies=[Depends(require_owner)])
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
            procedure.model_dump(exclude={"procedure_id"}),
            procedure.procedure_id
        )

    except Exception as error:
        print(
            "Procedure approval error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Database or embedding service error."
        )

    if saved is None:
        raise HTTPException(
            status_code=404,
            detail="Procedure not found."
        )

    return {
        "status": "approved",
        "procedure_id": saved.id,
        "title": saved.title,
        "version": saved.version,
        "last_confirmed": saved.last_confirmed
    }


@app.post("/api/query", dependencies=[Depends(get_current_user)])
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