from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg://handoff_user:handoff_password@localhost:5432/handoff"

engine = create_engine(DATABASE_URL)
