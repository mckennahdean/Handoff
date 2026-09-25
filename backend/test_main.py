from types import SimpleNamespace
from fastapi.testclient import TestClient
from backend.auth_service import get_current_user

import backend.main as main_module
import pytest

client = TestClient(main_module.app)

FAKE_OWNER = SimpleNamespace(
    id=1,
    name="Test Owner",
    email="owner@test.com",
    role="owner"
)


@pytest.fixture(autouse=True)
def logged_in_as_owner():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_OWNER
    )
    yield
    main_module.app.dependency_overrides.clear()


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Handoff backend is running"
    }


def test_structure_procedure_empty_text():
    response = client.post(
        "/api/structure-procedure",
        json={
            "text": ""
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Transcript text cannot be empty."
    )


def test_query_empty_question():
    response = client.post(
        "/api/query",
        json={
            "question": ""
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Question cannot be empty."
    )


def test_upload_audio_invalid_file_type():
    response = client.post(
        "/api/upload-audio",
        files={
            "audio_file": (
                "test.txt",
                b"hello",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Unsupported audio file format."
    )


def test_approve_procedure_missing_steps():
    response = client.post(
        "/api/approve-procedure",
        json={
            "title": "Test Procedure",
            "steps": [],
            "warnings": []
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Procedure must contain at least one step."
    )


def test_structure_procedure_success(monkeypatch):
    def fake_structure_procedure(text):
        return {
            "title": "Cash Drawer Closing",
            "steps": [
                "Count the cash drawer.",
                "Compare the amount with the register."
            ],
            "warnings": [
                "Notify the manager if the totals do not match."
            ]
        }

    monkeypatch.setattr(
        main_module,
        "structure_procedure",
        fake_structure_procedure
    )

    response = client.post(
        "/api/structure-procedure",
        json={
            "text": "Count the drawer and compare it with the register."
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Cash Drawer Closing"
    assert len(response.json()["steps"]) == 2


def test_query_answered(monkeypatch):
    fake_procedure = SimpleNamespace(
        id=2,
        title="End of Day Cash Drawer Reconciliation",
        steps='["Count the cash drawer."]',
        warnings='["Notify the manager if totals do not match."]',
        last_confirmed="2026-09-12T14:50:59"
    )

    def fake_find_best_matching_procedure(question):
        return fake_procedure, 0.85

    def fake_answer_question(question, procedure):
        return (
            "Notify the manager before closing."
        )

    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        fake_find_best_matching_procedure
    )

    monkeypatch.setattr(
        main_module,
        "answer_question_from_procedure",
        fake_answer_question
    )

    response = client.post(
        "/api/query",
        json={
            "question": (
                "What should I do if the cash drawer does not match?"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "answered"
    assert data["procedure_id"] == 2
    assert data["similarity"] == 0.85
    assert data["source_procedure"] == (
        "End of Day Cash Drawer Reconciliation"
    )


def test_query_abstains_and_logs_gap(monkeypatch):
    fake_procedure = SimpleNamespace(
        id=2,
        title="End of Day Cash Drawer Reconciliation",
        steps='["Count the cash drawer."]',
        warnings='[]',
        last_confirmed="2026-09-12T14:50:59"
    )

    logged_gap = {}

    def fake_find_best_matching_procedure(question):
        return fake_procedure, 0.40

    def fake_log_gap(question, similarity):
        logged_gap["question"] = question
        logged_gap["similarity"] = similarity

    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        fake_find_best_matching_procedure
    )

    monkeypatch.setattr(
        main_module,
        "log_gap",
        fake_log_gap
    )

    response = client.post(
        "/api/query",
        json={
            "question": "How do I request vacation time?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_documented"
    assert data["gap_logged"] is True
    assert data["similarity"] == 0.40

    assert logged_gap["question"] == (
        "How do I request vacation time?"
    )

    assert logged_gap["similarity"] == 0.40

    # ---------- Drafts and the Approval Gate ----------

FAKE_EMPLOYEE = SimpleNamespace(
    id=2,
    name="Test Employee",
    email="emp@test.com",
    role="employee"
)


def fake_procedure(status):
    return SimpleNamespace(
        id=7,
        title="Pending Draft",
        steps='["Step one."]',
        warnings="[]",
        status=status,
        version=1,
        capture_method="manual",
        gap_questions='["What if the customer has no receipt?"]',
        last_confirmed="2026-09-24T12:00:00"
    )


def test_owner_can_view_pending_draft(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "get_procedure",
        lambda procedure_id: fake_procedure("pending")
    )

    response = client.get("/api/procedures/7")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "pending"
    assert data["steps"] == ["Step one."]
    assert data["last_confirmed"] is None
    assert data["gap_questions"] == [
        "What if the customer has no receipt?"
    ]


def test_employee_cannot_view_pending_draft(monkeypatch):
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    monkeypatch.setattr(
        main_module,
        "get_procedure",
        lambda procedure_id: fake_procedure("pending")
    )

    response = client.get("/api/procedures/7")

    assert response.status_code == 404


def test_employee_procedure_list_excludes_drafts(monkeypatch):
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    received = {}

    def fake_get_procedures(include_pending):
        received["include_pending"] = include_pending
        return []

    monkeypatch.setattr(
        main_module,
        "get_procedures",
        fake_get_procedures
    )

    response = client.get("/api/procedures")

    assert response.status_code == 200
    assert received["include_pending"] is False


def test_create_draft_returns_pending_id(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "save_draft",
        lambda data: SimpleNamespace(id=7, status="pending")
    )

    response = client.post(
        "/api/procedures/drafts",
        json={
            "title": "Pending Draft",
            "steps": ["Step one."],
            "warnings": [],
            "capture_method": "manual"
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "procedure_id": 7,
        "status": "pending"
    }


def test_approve_missing_draft_returns_404(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "save_procedure",
        lambda data, procedure_id=None: None
    )

    response = client.post(
        "/api/approve-procedure",
        json={
            "procedure_id": 999,
            "title": "Missing",
            "steps": ["Step one."],
            "warnings": []
        }
    )

    assert response.status_code == 404

    # ---------- Knowledge gaps ----------

def test_answer_threshold_comes_from_config(monkeypatch):
    monkeypatch.setattr(main_module, "ANSWER_THRESHOLD", 0.90)

    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        lambda question: (fake_procedure("approved"), 0.85)
    )

    monkeypatch.setattr(
        main_module,
        "log_gap",
        lambda question, similarity: None
    )

    response = client.post(
        "/api/query",
        json={"question": "What is the refund limit?"}
    )

    assert response.json()["status"] == "not_documented"


def test_owner_can_dismiss_gap(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "dismiss_gap",
        lambda gap_id: gap_id
    )

    response = client.post("/api/gaps/3/dismiss")

    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"


def test_dismiss_missing_gap_returns_404(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "dismiss_gap",
        lambda gap_id: None
    )

    response = client.post("/api/gaps/999/dismiss")

    assert response.status_code == 404


def test_employee_cannot_dismiss_gap():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    response = client.post("/api/gaps/3/dismiss")

    assert response.status_code == 403

def test_owner_can_delete_procedure(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "delete_procedure",
        lambda procedure_id: 2
    )

    response = client.delete("/api/procedures/5")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert response.json()["gaps_reopened"] == 2


def test_delete_with_no_reopened_gaps_succeeds(monkeypatch):
    # 0 reopened gaps is falsy; the route must check "is None".
    monkeypatch.setattr(
        main_module,
        "delete_procedure",
        lambda procedure_id: 0
    )

    response = client.delete("/api/procedures/5")

    assert response.status_code == 200


def test_delete_missing_procedure_returns_404(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "delete_procedure",
        lambda procedure_id: None
    )

    response = client.delete("/api/procedures/999")

    assert response.status_code == 404


def test_employee_cannot_delete_procedure():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    response = client.delete("/api/procedures/5")

    assert response.status_code == 403

# ---------- Honest abstention ----------

def test_ai_refusal_becomes_logged_abstention(monkeypatch):
    from backend.gemini_service import NOT_DOCUMENTED_REPLY

    logged = {}

    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        lambda question: (fake_procedure("approved"), 0.85)
    )

    monkeypatch.setattr(
        main_module,
        "answer_question_from_procedure",
        lambda question, procedure: NOT_DOCUMENTED_REPLY
    )

    def fake_log_gap(question, similarity):
        logged["question"] = question

    monkeypatch.setattr(main_module, "log_gap", fake_log_gap)

    response = client.post(
        "/api/query",
        json={"question": "How often do we descale the machine?"}
    )

    data = response.json()

    assert data["status"] == "not_documented"
    assert data["gap_logged"] is True
    assert logged["question"] == "How often do we descale the machine?"


def test_gap_logged_is_false_when_logging_fails(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        lambda question: (fake_procedure("approved"), 0.40)
    )

    def broken_log_gap(question, similarity):
        raise RuntimeError("database down")

    monkeypatch.setattr(main_module, "log_gap", broken_log_gap)

    response = client.post(
        "/api/query",
        json={"question": "How do I request vacation?"}
    )

    assert response.json()["gap_logged"] is False


def test_retrieval_outage_returns_503(monkeypatch):
    def outage(question):
        raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(
        main_module,
        "find_best_matching_procedure",
        outage
    )

    response = client.post(
        "/api/query",
        json={"question": "How do I clean the espresso machine?"}
    )

    assert response.status_code == 503

from backend.db_service import procedure_chunk_texts

def test_chunks_cover_every_step_and_warning_with_title():
    chunks = procedure_chunk_texts({
        "title": "Closing the Cafe",
        "steps": ["Lock the front door.", "Count the till."],
        "warnings": ["Never leave cash overnight."]
    })

    assert chunks == [
        "Closing the Cafe: Lock the front door.",
        "Closing the Cafe: Count the till.",
        "Closing the Cafe: Never leave cash overnight."
    ]