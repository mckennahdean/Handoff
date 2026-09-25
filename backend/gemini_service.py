import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors


load_dotenv()

# Models are configurable in .env so they can be switched without
# code changes. Check each model's limits at https://ai.dev/rate-limit
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.1-flash-lite")
STRUCTURE_MODEL = os.getenv("GEMINI_STRUCTURE_MODEL", TEXT_MODEL)
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Owners never face more than this many follow-up questions.
MAX_GAP_QUESTIONS = 5

# Temporary Google errors (5xx) are retried this many times in total.
MAX_ATTEMPTS = 3

# The exact reply the answer prompt uses when the retrieved
# procedure does not contain the answer. Checked by the API.
NOT_DOCUMENTED_REPLY = (
    "This information is not documented in the retrieved procedure."
)

client = None


class MergeAlteredContentError(Exception):
    """Raised when the AI changes or drops the owner's existing text."""


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


def _is_transient(error) -> bool:
    # Only 5xx errors (a temporary problem on Google's side) are
    # worth an immediate retry. 429 means a quota or rate limit,
    # which will not clear within a few seconds.
    return isinstance(error, errors.ServerError)


def _with_retry(call, **kwargs):
    """Run a Gemini call, retrying temporary failures with backoff."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return call(**kwargs)

        except errors.APIError as error:
            if attempt == MAX_ATTEMPTS or not _is_transient(error):
                raise

            time.sleep(2 ** (attempt - 1))  # wait 1s, then 2s


def _generate(**kwargs):
    return _with_retry(get_client().models.generate_content, **kwargs)


def embed_text(text: str) -> list:
    response = _with_retry(
        get_client().models.embed_content,
        model=EMBEDDING_MODEL,
        contents=text
    )

    return response.embeddings[0].values


def _json_config(temperature=None):
    # JSON mode forces Gemini to return valid JSON, so responses
    # can no longer arrive wrapped in markdown code fences.
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=temperature
    )


def _clean_list(value) -> list:
    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]


def _keeps_original_items(original: list, updated: list) -> bool:
    """True if every original item still appears unchanged, in order.

    New items may be inserted anywhere, but nothing the owner
    wrote may be reworded, removed, or reordered.
    """
    remaining = iter(item.strip() for item in updated)

    return all(
        item.strip() in remaining
        for item in original
    )


def structure_procedure(text: str):
    response = _generate(
        model=STRUCTURE_MODEL,
        config=_json_config(),
        contents=f"""
You are helping a small business owner document a procedure
they explained out loud.

Task 1: Structure the explanation into a title, ordered steps,
and warnings. Use ONLY information the owner provided. Do not
invent steps.

Task 2: Identify knowledge gaps. Experts often skip things they
do automatically. Look for missing information a new employee
would need: exceptions (what if something goes wrong?), who to
contact, limits or thresholds, where things are located, and
steps implied but never stated. Write each gap as a short,
specific question to the owner. Return at most
{MAX_GAP_QUESTIONS} questions, most important first. If the
procedure is complete, return an empty list.

Return JSON in exactly this format:

{{
  "title": "string",
  "steps": ["step 1", "step 2"],
  "warnings": ["warning 1"],
  "gap_questions": ["question 1"]
}}

Owner explanation:
{text}
"""
    )

    data = json.loads(response.text)

    return {
        "title": str(data.get("title", "")).strip() or "Untitled Procedure",
        "steps": _clean_list(data.get("steps")),
        "warnings": _clean_list(data.get("warnings")),
        # Enforced in code too: never trust the model to follow a limit.
        "gap_questions": _clean_list(
            data.get("gap_questions")
        )[:MAX_GAP_QUESTIONS]
    }


def merge_gap_answers(
    title: str,
    steps: list,
    warnings: list,
    answered_gaps: list
):
    """Fold the owner's gap answers into the procedure.

    Insert-only: existing steps and warnings must come back
    word for word, or the merge is rejected.
    """
    steps = [step for step in steps if step.strip()]
    warnings = [warning for warning in warnings if warning.strip()]

    answers_text = "\n".join(
        f"Q: {gap['question']}\nA: {gap['answer']}"
        for gap in answered_gaps
    )

    response = _generate(
        model=TEXT_MODEL,
        config=_json_config(temperature=0),
        contents=f"""
You are updating a small business procedure with answers the
owner gave to follow-up questions.

Rules:
- Copy every existing step and warning EXACTLY as written.
  Do not reword, reorder, merge, or remove any of them.
- Add the new information from the answers as NEW steps
  (inserted where they belong in the sequence) or NEW warnings
  (for exceptions and cautions).
- Use ONLY the owner's answers. Do not invent information.
- Do not ask questions.

Return JSON in exactly this format:

{{
  "steps": ["step 1", "step 2"],
  "warnings": ["warning 1"]
}}

Procedure title: {title}

Existing steps (JSON):
{json.dumps(steps)}

Existing warnings (JSON):
{json.dumps(warnings)}

Owner's answers:
{answers_text}
"""
    )

    data = json.loads(response.text)

    new_steps = _clean_list(data.get("steps"))
    new_warnings = _clean_list(data.get("warnings"))

    if not (
        _keeps_original_items(steps, new_steps)
        and _keeps_original_items(warnings, new_warnings)
    ):
        raise MergeAlteredContentError(
            "The AI changed existing procedure text."
        )

    return {
        "steps": new_steps,
        "warnings": new_warnings
    }


def answer_question_from_procedure(
    question: str,
    procedure
):
    procedure_text = (
        f"Title: {procedure.title}\n"
        f"Steps: {procedure.steps}\n"
        f"Warnings: {procedure.warnings}"
    )

    response = _generate(
        model=TEXT_MODEL,
        # Temperature 0: the same question over the same procedure
        # should always get the same grounded answer.
        config=types.GenerateContentConfig(temperature=0),
        contents=f"""
You are answering an employee question using ONLY the procedure below.

Do not use outside knowledge.
Do not guess.
If the procedure does not contain the answer, reply with exactly:
"{NOT_DOCUMENTED_REPLY}"

Procedure:
{procedure_text}

Employee question:
{question}
"""
    )

    return response.text.strip()


def transcribe_audio(file_path: str):
    gemini_client = get_client()

    audio_file = gemini_client.files.upload(
        file=Path(file_path)
    )

    response = _generate(
        model=TEXT_MODEL,
        contents=[
            audio_file,
            "Transcribe this audio accurately. Return only the transcript text."
        ]
    )

    return response.text