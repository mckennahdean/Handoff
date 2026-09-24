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