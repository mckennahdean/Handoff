import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

response = client.models.embed_content(
    model="gemini-embedding-2",
    contents="Customer return without a receipt"
)

embedding = response.embeddings[0].values

print("Embedding length:", len(embedding))
print("First 5 numbers:", embedding[:5])