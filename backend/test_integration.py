"""Integration tests: the real db_service code against a real
PostgreSQL + pgvector database.

The unit tests mock the database layer, which left db_service.py at
25% coverage. These tests run the real SQL: chunk storage, chunk
retrieval, gap grouping, auto-resolve, and delete with reopen.

Gemini is replaced with a deterministic fake embedding, so the tests
are free, fast, and repeatable. They need their own database and
skip themselves when TEST_DATABASE_URL is not set.
"""
import json
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

import backend.db_service as db_service
from backend.models import Base, Gap, ProcedureChunk

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set TEST_DATABASE_URL to run integration tests."
)

TOPICS = ["till", "descale", "invoice", "fridge"]
VECTOR_SIZE = 3072

CLOSING = {
    "title": "Closing the Cafe",
    "steps": ["Count the till with a coworker.", "Lock the back door."],
    "warnings": ["Never leave the till unlocked."]
}

RECEIVING = {
    "title": "Receiving Deliveries",
    "steps": ["Check the invoice.", "Sign the invoice."],
    "warnings": []
}


def fake_vector(text_value: str) -> list:
    """Deterministic stand-in for a Gemini embedding.

    Texts sharing a topic word point the same way (similarity near
    1.0); texts with different topics are nearly unrelated (near
    0.0). Test questions always include a topic word.
    """
    lowered = text_value.lower()
    vector = [0.0] * VECTOR_SIZE

    for index, topic in enumerate(TOPICS):
        if topic in lowered:
            vector[index] = 1.0

    # A small shared value keeps every vector non-zero.
    vector[-1] = 0.1

    return vector


@pytest.fixture
def db(monkeypatch):
    # Every test deletes all tables, so refuse anything that is not
    # clearly a test database. Protects the real demo data.
    database_name = TEST_DATABASE_URL.rsplit("/", 1)[-1]

    if "test" not in database_name:
        pytest.fail(
            f"TEST_DATABASE_URL must name a test database, "
            f"not '{database_name}'."
        )

    engine = create_engine(TEST_DATABASE_URL)

    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()

    # A clean database for every test, so tests never affect each other.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(db_service, "engine", engine)
    monkeypatch.setattr(db_service, "embed_text", fake_vector)
    monkeypatch.setattr(
        db_service,
        "embed_texts",
        lambda texts: [fake_vector(t) for t in texts]
    )

    yield engine

    engine.dispose()


def count(engine, model, *conditions):
    statement = select(func.count()).select_from(model)

    if conditions:
        statement = statement.where(*conditions)

    with Session(engine) as session:
        return session.scalar(statement)


def test_approving_creates_one_chunk_per_step_and_warning(db):
    procedure = db_service.save_procedure(CLOSING)

    assert procedure.status == "approved"
    assert procedure.version == 1
    assert count(
        db, ProcedureChunk, ProcedureChunk.procedure_id == procedure.id
    ) == 3


def test_reapproving_replaces_chunks_and_bumps_version(db):
    first = db_service.save_procedure(CLOSING)

    edited = {**CLOSING, "steps": ["Count the till with a coworker."]}
    second = db_service.save_procedure(edited, first.id)

    assert second.version == 2
    # One step plus one warning; the removed step's chunk is gone.
    assert count(
        db, ProcedureChunk, ProcedureChunk.procedure_id == first.id
    ) == 2


def test_retrieval_returns_procedure_with_best_matching_chunk(db):
    closing = db_service.save_procedure(CLOSING)
    db_service.save_procedure(RECEIVING)

    procedure, similarity = db_service.find_best_matching_procedure(
        "Where do I record the till count?"
    )

    assert procedure.id == closing.id
    assert similarity > 0.9


def test_drafts_are_never_retrieved(db):
    db_service.save_draft(CLOSING)

    procedure, similarity = db_service.find_best_matching_procedure(
        "Where do I record the till count?"
    )

    assert procedure is None
    assert similarity is None


def test_similar_questions_are_grouped_and_every_wording_kept(db):
    db_service.log_gap("How often should we descale the machine?", 0.5)
    db_service.log_gap("What descaler do we use?", 0.5)
    db_service.log_gap("Where does the signed invoice go?", 0.5)

    with Session(db) as session:
        gaps = session.scalars(select(Gap).order_by(Gap.id)).all()

    assert len(gaps) == 2
    assert gaps[0].frequency_count == 2
    assert json.loads(gaps[0].variants) == ["What descaler do we use?"]
    assert gaps[1].frequency_count == 1


def test_approving_a_procedure_resolves_the_gap_it_answers(db):
    gap = db_service.log_gap("Where do I record the till count?", 0.4)

    procedure = db_service.save_procedure(CLOSING)

    with Session(db) as session:
        stored = session.get(Gap, gap.id)

    assert procedure.resolved_gap_count == 1
    assert stored.status == "resolved"
    assert stored.resolved_by_procedure_id == procedure.id


def test_deleting_a_procedure_reopens_gaps_and_removes_chunks(db):
    gap = db_service.log_gap("Where do I record the till count?", 0.4)
    procedure = db_service.save_procedure(CLOSING)

    reopened = db_service.delete_procedure(procedure.id)

    with Session(db) as session:
        stored = session.get(Gap, gap.id)

    assert reopened == 1
    assert stored.status == "open"
    assert stored.resolved_by_procedure_id is None
    # ON DELETE CASCADE removed the chunks inside Postgres itself.
    assert count(db, ProcedureChunk) == 0