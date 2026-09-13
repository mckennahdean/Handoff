from sqlalchemy import text

from backend.database import engine
from backend.models import Base

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(engine)

    print("Database tables created.")