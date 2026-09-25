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
        for statement in [
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS embedding vector(3072);",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open';",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS last_asked_at TIMESTAMP;",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS resolved_by_procedure_id INTEGER;",
        ]:
            conn.execute(text(statement))
        conn.commit()

    print("Database tables created.")