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
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

import backend.db_service as db_service
import backend.auth_service as auth_service
from backend.models import Base, Gap, ProcedureChunk, User
import backend.seed_demo as seed_demo
from backend.create_tables import create_tables

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


def test_get_gaps_lists_open_first_with_variants_and_resolver_title(db):
    db_service.log_gap("Where do I record the till count?", 0.4)
    db_service.log_gap("Who counts the till at night?", 0.4)
    db_service.log_gap("How often should we descale?", 0.3)

    procedure = db_service.save_procedure(CLOSING)

    gaps = db_service.get_gaps()

    # Open first, even though the resolved gap was asked more often.
    assert [gap["status"] for gap in gaps] == ["open", "resolved"]

    descale, till = gaps
    assert descale["question"] == "How often should we descale?"
    assert descale["variants"] == []
    assert descale["resolved_by_title"] is None

    assert till["frequency_count"] == 2
    assert till["variants"] == ["Who counts the till at night?"]
    assert till["resolved_by_procedure_id"] == procedure.id
    assert till["resolved_by_title"] == "Closing the Cafe"


def test_dismissing_a_gap_marks_it_dismissed(db):
    gap = db_service.log_gap("How often should we descale?", 0.3)

    assert db_service.dismiss_gap(gap.id) == gap.id
    assert db_service.dismiss_gap(9999) is None

    with Session(db) as session:
        stored = session.get(Gap, gap.id)

    assert stored.status == "dismissed"
    assert stored.resolved_at is not None


def test_asking_again_after_dismissal_opens_a_new_gap(db):
    gap = db_service.log_gap("How often should we descale?", 0.3)
    db_service.dismiss_gap(gap.id)

    again = db_service.log_gap("When do we descale the machine?", 0.3)

    assert again.id != gap.id
    assert again.status == "open"
    assert again.frequency_count == 1


def test_seed_demo_adds_each_procedure_once(db):
    first_run = seed_demo.seed(pause_seconds=0)
    second_run = seed_demo.seed(pause_seconds=0)

    assert first_run == 7
    assert second_run == 0
    assert len(db_service.get_procedures()) == 7


def test_user_management_against_real_database(db, monkeypatch):
    # The shared fixture points db_service at the test database;
    # auth_service has its own engine reference, so point it too.
    monkeypatch.setattr(auth_service, "engine", db)

    with Session(db) as session:
        owner = User(
            name="Olive Owner",
            email="olive@test.com",
            password_hash="not-a-real-hash",
            role="owner"
        )
        employee = User(
            name="Eddie Employee",
            email="eddie@test.com",
            password_hash="not-a-real-hash",
            role="employee"
        )
        session.add_all([owner, employee])
        session.commit()
        owner_id, employee_id = owner.id, employee.id

    names = [user.name for user in auth_service.list_users()]
    assert names == ["Eddie Employee", "Olive Owner"]

    assert auth_service.set_user_role(employee_id, "owner").role == "owner"
    assert auth_service.set_user_role(9999, "owner") is None

    # Owners are never deleted.
    assert auth_service.delete_employee(owner_id) is False

    auth_service.set_user_role(employee_id, "employee")
    assert auth_service.delete_employee(employee_id) is True
    assert auth_service.delete_employee(employee_id) is None


def column_types(engine):
    """Every column's type and nullability, for before/after checks."""
    with engine.connect() as connection:
        return connection.execute(text(
            "SELECT table_name, column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "ORDER BY table_name, column_name"
        )).all()


def test_create_tables_is_safe_to_run_repeatedly(db):
    create_tables(db)
    before = column_types(db)

    assert create_tables(db) == []
    assert column_types(db) == before


def test_create_tables_converts_old_timestamps_without_shifting_them(db):
    # Recreate the pre-migration schema: a naive timestamp column
    # holding a UTC wall-clock value.
    with db.connect() as connection:
        connection.execute(text(
            "ALTER TABLE business ALTER COLUMN created_at "
            "TYPE TIMESTAMP WITHOUT TIME ZONE"
        ))
        connection.execute(text(
            "INSERT INTO business (name, invite_code, created_at) "
            "VALUES ('Test Cafe', 'TESTCODE', '2026-09-25 12:00:00')"
        ))
        connection.commit()

    assert create_tables(db) == ["business.created_at"]

    with db.connect() as connection:
        data_type = connection.execute(text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'business' "
            "AND column_name = 'created_at'"
        )).scalar()
        created_at = connection.execute(text(
            "SELECT created_at FROM business"
        )).scalar()

    assert data_type == "timestamp with time zone"
    assert created_at == datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)

    # A second run finds nothing left to convert.
    assert create_tables(db) == []


PASSWORD = "Correct-Horse-Battery-9"


@pytest.fixture
def auth_db(db, monkeypatch):
    # auth_service has its own engine reference; point it at the
    # test database. A fixed test secret keeps CI independent of .env.
    monkeypatch.setattr(auth_service, "engine", db)
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "integration-test-secret-key-0123456789abcdef"
    )
    return db


def test_owner_signup_stores_an_argon2_hash_never_the_password(auth_db):
    owner = auth_service.create_owner_account(
        "Olive Owner", "olive@test.com", PASSWORD, "Test Cafe"
    )

    assert owner.role == "owner"
    assert auth_service.count_users() == 1

    stored = auth_service.get_user_by_email("olive@test.com").password_hash
    assert stored.startswith("$argon2id$")
    assert PASSWORD not in stored

    business = auth_service.get_business()
    assert business.name == "Test Cafe"
    assert len(business.invite_code) == auth_service.INVITE_CODE_LENGTH


def test_login_gives_one_answer_for_wrong_password_and_unknown_email(
    auth_db, monkeypatch
):
    auth_service.create_owner_account(
        "Olive Owner", "olive@test.com", PASSWORD, "Test Cafe"
    )

    user = auth_service.authenticate_user("olive@test.com", PASSWORD)
    assert user.email == "olive@test.com"

    # Record which hashes get checked, to prove an unknown email
    # still pays for one real Argon2 check (the timing defense).
    checked = []
    real_verify = auth_service.verify_password
    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, password_hash: (
            checked.append(password_hash)
            or real_verify(password, password_hash)
        )
    )

    assert auth_service.authenticate_user(
        "olive@test.com", "Wrong-Password-12"
    ) is None
    assert auth_service.authenticate_user(
        "nobody@test.com", PASSWORD
    ) is None

    assert len(checked) == 2
    assert checked[1] == auth_service.DUMMY_HASH


def test_invite_codes_are_checked_against_the_database(auth_db):
    # No business yet, so no code can be valid.
    assert auth_service.invite_code_is_valid("ABCD2345") is False

    auth_service.create_owner_account(
        "Olive Owner", "olive@test.com", PASSWORD, "Test Cafe"
    )
    code = auth_service.get_business().invite_code

    assert auth_service.invite_code_is_valid(code)
    # Typed casually, with spaces and lowercase, it still works.
    assert auth_service.invite_code_is_valid(f"  {code.lower()} ")
    assert auth_service.invite_code_is_valid("WRONG234") is False

    employee = auth_service.create_employee_account(
        "Eddie Employee", "eddie@test.com", PASSWORD
    )
    assert employee.role == "employee"
    assert auth_service.count_users() == 2


def test_regenerating_the_invite_code_kills_the_old_one(auth_db):
    auth_service.create_owner_account(
        "Olive Owner", "olive@test.com", PASSWORD, "Test Cafe"
    )
    old_code = auth_service.get_business().invite_code

    new_code = auth_service.regenerate_invite_code()

    assert new_code != old_code
    assert auth_service.invite_code_is_valid(old_code) is False
    assert auth_service.invite_code_is_valid(new_code)


def test_the_database_not_the_token_decides_who_you_are(auth_db):
    auth_service.create_owner_account(
        "Olive Owner", "olive@test.com", PASSWORD, "Test Cafe"
    )
    employee = auth_service.create_employee_account(
        "Eddie Employee", "eddie@test.com", PASSWORD
    )

    # A token issued while Eddie was an owner says role "owner".
    promoted = auth_service.set_user_role(employee.id, "owner")
    token = auth_service.create_access_token(promoted)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=token
    )

    # Demoted after the token was issued: owner access ends now.
    auth_service.set_user_role(employee.id, "employee")
    user = auth_service.get_current_user(credentials)
    assert user.role == "employee"

    with pytest.raises(HTTPException) as denied:
        auth_service.require_owner(user)
    assert denied.value.status_code == 403

    # Deleted: the still-valid token no longer gets in at all.
    assert auth_service.delete_employee(employee.id) is True

    with pytest.raises(HTTPException) as refused:
        auth_service.get_current_user(credentials)
    assert refused.value.status_code == 401
    assert refused.value.detail == "User no longer exists."
