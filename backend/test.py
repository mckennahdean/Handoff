import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="""
    Turn this into simple numbered steps:

    When a customer returns an item, first ask for the receipt.
    Then check the purchase date.
    If they do not have a receipt, ask the manager.
    """
)

print(response.text)