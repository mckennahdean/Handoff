from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

import backend.auth_routes as auth_routes
import backend.main as main_module
from backend.auth_service import (
    INVITE_CODE_ALPHABET,
    INVITE_CODE_LENGTH,
    create_access_token,
    decode_access_token,
    generate_invite_code,
    get_current_user,
    hash_password,
    verify_password,
)


client = TestClient(main_module.app)

TEST_SECRET = "test-secret-key-for-pytest-only-0123456789"

FAKE_EMPLOYEE = SimpleNamespace(
    id=2,
    name="Test Employee",
    email="emp@test.com",
    role="employee"
)

VALID_PROCEDURE = {
    "title": "Test Procedure",
    "steps": ["Step one."],
    "warnings": []
}


@pytest.fixture(autouse=True)
def auth_test_setup(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    main_module.app.dependency_overrides.clear()
    yield
    main_module.app.dependency_overrides.clear()


def future_time():
    return datetime.now(timezone.utc) + timedelta(hours=1)


# ---------- Password hashing ----------

def test_password_is_hashed_not_stored_plain():
    hashed = hash_password("password123")

    assert hashed != "password123"
    assert hashed.startswith("$argon2")


def test_verify_password_accepts_correct_and_rejects_wrong():
    hashed = hash_password("password123")

    assert verify_password("password123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


# ---------- Tokens ----------

def test_token_round_trip():
    user = SimpleNamespace(id=5, role="owner")

    payload = decode_access_token(create_access_token(user))

    assert payload["sub"] == "5"
    assert payload["role"] == "owner"


def test_expired_token_is_rejected():
    expired_token = jwt.encode(
        {
            "sub": "1",
            "role": "owner",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        },
        TEST_SECRET,
        algorithm="HS256"
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Session expired. Please log in again."
    )


def test_forged_token_is_rejected():
    forged_token = jwt.encode(
        {"sub": "1", "role": "owner", "exp": future_time()},
        "attacker-guessed-secret-key-0123456789",
        algorithm="HS256"
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid authentication token."
    )


# ---------- Route protection ----------

def test_protected_route_without_token_returns_401():
    response = client.post(
        "/api/approve-procedure",
        json=VALID_PROCEDURE
    )

    assert response.status_code == 401


def test_employee_cannot_approve_procedure():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    response = client.post(
        "/api/approve-procedure",
        json=VALID_PROCEDURE
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Owner access required."


def test_employee_cannot_view_invite_code():
    main_module.app.dependency_overrides[get_current_user] = (
        lambda: FAKE_EMPLOYEE
    )

    response = client.get("/api/business/invite-code")

    assert response.status_code == 403


# ---------- Signup and login ----------

def test_signup_rejects_invalid_invite_code(monkeypatch):
    monkeypatch.setattr(auth_routes, "count_users", lambda: 1)
    monkeypatch.setattr(
        auth_routes,
        "invite_code_is_valid",
        lambda code: False
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Emp",
            "email": "emp@test.com",
            "password": "password123",
            "invite_code": "WRONG123"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid invite code."


def test_signup_rejects_short_password():
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Emp",
            "email": "emp@test.com",
            "password": "short"
        }
    )

    assert response.status_code == 400


def test_login_with_bad_credentials_returns_401(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda email, password: None
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "tom@test.com", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_invite_code_format():
    code = generate_invite_code()

    assert len(code) == INVITE_CODE_LENGTH
    assert all(char in INVITE_CODE_ALPHABET for char in code)