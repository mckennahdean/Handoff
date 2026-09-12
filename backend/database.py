import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://handoff_user:handoff_password@localhost:5432/handoff"
)

engine = create_engine(DATABASE_URL)