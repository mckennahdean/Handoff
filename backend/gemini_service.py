import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def structure_procedure(text: str):
    response = client.models.generate_content(
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