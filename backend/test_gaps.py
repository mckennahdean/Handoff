import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import backend.gemini_service as gemini_service
import backend.main as main_module
from backend.auth_service import get_current_user
from backend.gemini_service import (
    MAX_GAP_QUESTIONS,
    MergeAlteredContentError,
    _keeps_original_items,
    merge_gap_answers,
    structure_procedure,
)


client = TestClient(main_module.app)

FAKE_OWNER = SimpleNamespace(
    id=1,
    name="Test Owner",
    email="owner@test.com",
    role="owner"
)

ORIGINAL_STEPS = [
    "Check the receipt.",
    "Refund the customer."
]


@pytest.fixture(autouse=True)
def logged_in_as_owner():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_OWNER
    )
    yield
    main_module.app.dependency_overrides.clear()


def use_fake_gemini(monkeypatch, payload: dict):
    """Make every Gemini call return this JSON payload."""
    fake_models = SimpleNamespace(
        generate_content=lambda **kwargs: SimpleNamespace(
            text=json.dumps(payload)
        )
    )

    monkeypatch.setattr(
        gemini_service,
        "get_client",
        lambda: SimpleNamespace(models=fake_models)
    )


# ---------- Gap detection ----------

def test_structure_returns_gap_questions(monkeypatch):
    use_fake_gemini(monkeypatch, {
        "title": "Returns",
        "steps": ["Check the receipt."],
        "warnings": [],
        "gap_questions": ["What if there is no receipt?"]
    })

    result = structure_procedure("Check the receipt.")

    assert result["gap_questions"] == ["What if there is no receipt?"]


def test_structure_caps_gap_questions_at_five(monkeypatch):
    use_fake_gemini(monkeypatch, {
        "title": "Returns",
        "steps": ["Check the receipt."],
        "warnings": [],
        "gap_questions": [f"Question {n}?" for n in range(1, 9)]
    })

    result = structure_procedure("Check the receipt.")

    assert len(result["gap_questions"]) == MAX_GAP_QUESTIONS
    assert result["gap_questions"][0] == "Question 1?"


def test_structure_handles_missing_gap_questions(monkeypatch):
    use_fake_gemini(monkeypatch, {
        "title": "Returns",
        "steps": ["Check the receipt."],
        "warnings": []
    })

    result = structure_procedure("Check the receipt.")

    assert result["gap_questions"] == []


# ---------- Merge guardrail ----------

def test_guardrail_accepts_inserted_steps():
    assert _keeps_original_items(
        ORIGINAL_STEPS,
        [
            "Check the receipt.",
            "If there is no receipt, offer store credit.",
            "Refund the customer."
        ]
    )


def test_guardrail_rejects_reworded_steps():
    assert not _keeps_original_items(
        ORIGINAL_STEPS,
        ["Verify the receipt.", "Refund the customer."]
    )


def test_guardrail_rejects_reordered_steps():
    assert not _keeps_original_items(
        ORIGINAL_STEPS,
        ["Refund the customer.", "Check the receipt."]
    )


def test_merge_adds_answers_without_changing_steps(monkeypatch):
    use_fake_gemini(monkeypatch, {
        "steps": [
            "Check the receipt.",
            "If there is no receipt, offer store credit.",
            "Refund the customer."
        ],
        "warnings": []
    })

    result = merge_gap_answers(
        "Returns",
        ORIGINAL_STEPS,
        [],
        [{
            "question": "What if there is no receipt?",
            "answer": "Offer store credit."
        }]
    )

    assert len(result["steps"]) == 3
    assert result["steps"][0] == "Check the receipt."


def test_merge_rejects_ai_that_rewrites_steps(monkeypatch):
    use_fake_gemini(monkeypatch, {
        "steps": ["Verify the receipt.", "Refund the customer."],
        "warnings": []
    })

    with pytest.raises(MergeAlteredContentError):
        merge_gap_answers(
            "Returns",
            ORIGINAL_STEPS,
            [],
            [{"question": "What if?", "answer": "Offer store credit."}]
        )


# ---------- Merge endpoint ----------

def test_merge_endpoint_requires_an_answer():
    response = client.post(
        "/api/procedures/merge-answers",
        json={
            "title": "Returns",
            "steps": ORIGINAL_STEPS,
            "warnings": [],
            "answers": [{"question": "What if?", "answer": "   "}]
        }
    )

    assert response.status_code == 400


def test_merge_endpoint_returns_502_when_ai_alters_steps(monkeypatch):
    def fake_merge(*args):
        raise MergeAlteredContentError("changed")

    monkeypatch.setattr(
        main_module,
        "merge_gap_answers",
        fake_merge
    )

    response = client.post(
        "/api/procedures/merge-answers",
        json={
            "title": "Returns",
            "steps": ORIGINAL_STEPS,
            "warnings": [],
            "answers": [{
                "question": "What if there is no receipt?",
                "answer": "Offer store credit."
            }]
        }
    )

    assert response.status_code == 502