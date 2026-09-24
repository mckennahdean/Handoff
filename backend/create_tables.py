from sqlalchemy import text

from backend.database import engine
from backend.models import Base

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(engine)

    # Lightweight migrations for databases created before these
    # columns changed. Each statement is safe to run repeatedly.
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE procedures "
            "ALTER COLUMN embedding DROP NOT NULL;"
        ))
        conn.execute(text(
            "ALTER TABLE procedures "
            "ADD COLUMN IF NOT EXISTS capture_method VARCHAR(20);"
        ))
        conn.execute(text(
            "ALTER TABLE procedures "
            "ADD COLUMN IF NOT EXISTS gap_questions TEXT;"
        ))
        conn.commit()

    print("Database tables created.")