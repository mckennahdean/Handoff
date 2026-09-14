import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai


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


def structure_procedure(text: str):
    gemini_client = get_client()

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
You are helping a small business document procedures.

Return ONLY valid JSON in this exact format:

{{
  "title": "string",
  "steps": ["step 1", "step 2"],
  "warnings": ["warning 1"]
}}

Do not add markdown.
Do not add explanations outside the JSON.

Owner explanation:
{text}
"""
    )

    return json.loads(response.text)


def answer_question_from_procedure(
    question: str,
    procedure
):
    gemini_client = get_client()

    procedure_text = (
        f"Title: {procedure.title}\n"
        f"Steps: {procedure.steps}\n"
        f"Warnings: {procedure.warnings}"
    )

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
You are answering an employee question using ONLY the procedure below.

Do not use outside knowledge.
Do not guess.
If the procedure does not contain the answer, say:
"This information is not documented in the retrieved procedure."

Procedure:
{procedure_text}

Employee question:
{question}
"""
    )

    return response.text


def transcribe_audio(file_path: str):
    gemini_client = get_client()

    audio_file = gemini_client.files.upload(
        file=Path(file_path)
    )

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            audio_file,
            "Transcribe this audio accurately. Return only the transcript text."
        ]
    )

    return response.text