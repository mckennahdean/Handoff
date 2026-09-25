from sqlalchemy import text

from backend.database import engine
from backend.models import Base

# Timestamp columns that must be timezone-aware (TIMESTAMPTZ)
# so the API returns UTC offsets the browser can convert.
TIMESTAMP_COLUMNS = [
    ("procedures", "last_confirmed"),
    ("gaps", "created_at"),
    ("gaps", "last_asked_at"),
    ("gaps", "resolved_at"),
    ("users", "created_at"),
    ("business", "created_at"),
]

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
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS last_asked_at TIMESTAMPTZ;",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;",
            "ALTER TABLE gaps ADD COLUMN IF NOT EXISTS resolved_by_procedure_id INTEGER;",
        ]:
            conn.execute(text(statement))

        # Convert naive timestamps (stored as UTC wall-clock time)
        # to TIMESTAMPTZ. The type check makes this a no-op once a
        # column is already converted, so reruns never shift dates.
        for table, column in TIMESTAMP_COLUMNS:
            data_type = conn.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name = :table AND column_name = :column"
                ),
                {"table": table, "column": column},
            ).scalar()

            if data_type == "timestamp without time zone":
                conn.execute(text(
                    f"ALTER TABLE {table} ALTER COLUMN {column} "
                    f"TYPE TIMESTAMPTZ USING {column} AT TIME ZONE 'UTC';"
                ))
                print(f"Converted {table}.{column} to TIMESTAMPTZ")

        conn.commit()

    print("Database tables created.")