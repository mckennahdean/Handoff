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