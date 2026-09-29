from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient

import backend.auth_routes as auth_routes
import backend.main as main_module
from backend.auth_service import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    password_problems,
    verify_password,
)


client = TestClient(main_module.app)

TEST_SECRET = "test-secret-key-for-pytest-only-0123456789"
STRONG_PASSWORD = "Handoff-Test-2026"

FAKE_EMPLOYEE = SimpleNamespace(
    id=2,
    name="Test Employee",
    email="emp@test.com",
    role="employee",
    status="active"
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


# ---------- Signup and login ----------

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
    assert response.json()["detail"].startswith("Invalid email or password.")


# ---------- Password policy ----------

@pytest.mark.parametrize(
    "weak_password",
    [
        "Sh0rt!pass",          # too short (10 characters)
        "alllowercase-2026",   # no uppercase
        "ALLUPPERCASE-2026",   # no lowercase
        "No-Numbers-Here!",    # no number
        "NoSpecialChars2026",  # no special character
    ],
)
def test_weak_passwords_are_rejected(weak_password):
    assert password_problems(weak_password) != []


def test_strong_password_passes():
    assert password_problems(STRONG_PASSWORD) == []


def test_overly_long_password_is_rejected():
    assert password_problems("Aa1!" * 40) != []



# ---------- User management ----------

FAKE_OWNER = SimpleNamespace(
    id=1,
    name="Test Owner",
    email="owner@test.com",
    role="owner",
    status="active"
)


def log_in_as(user):
    main_module.app.dependency_overrides[get_current_user] = lambda: user


def test_owner_can_list_users(monkeypatch):
    log_in_as(FAKE_OWNER)
    monkeypatch.setattr(
        auth_routes, "list_users", lambda: [FAKE_OWNER, FAKE_EMPLOYEE]
    )

    response = client.get("/api/business/users")

    assert response.status_code == 200
    assert [user["email"] for user in response.json()] == [
        "owner@test.com",
        "emp@test.com"
    ]


def test_employee_cannot_manage_users():
    log_in_as(FAKE_EMPLOYEE)

    responses = [
        client.get("/api/business/users"),
        client.patch(
            "/api/business/users/1/role", json={"role": "employee"}
        ),
        client.delete("/api/business/users/1"),
    ]

    assert [response.status_code for response in responses] == [
        403, 403, 403
    ]


def test_owner_can_change_another_users_role(monkeypatch):
    log_in_as(FAKE_OWNER)
    promoted = SimpleNamespace(**{**vars(FAKE_EMPLOYEE), "role": "owner"})
    monkeypatch.setattr(
        auth_routes, "set_user_role", lambda user_id, role: promoted
    )

    response = client.patch(
        "/api/business/users/2/role", json={"role": "owner"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "owner"


def test_owner_cannot_change_their_own_role(monkeypatch):
    log_in_as(FAKE_OWNER)
    calls = []
    monkeypatch.setattr(
        auth_routes,
        "set_user_role",
        lambda user_id, role: calls.append(user_id)
    )

    response = client.patch(
        "/api/business/users/1/role", json={"role": "employee"}
    )

    assert response.status_code == 400
    # Rejected before the database was touched.
    assert calls == []


def test_role_must_be_owner_or_employee():
    log_in_as(FAKE_OWNER)

    response = client.patch(
        "/api/business/users/2/role", json={"role": "admin"}
    )

    assert response.status_code == 400


def test_changing_role_of_missing_user_returns_404(monkeypatch):
    log_in_as(FAKE_OWNER)
    monkeypatch.setattr(
        auth_routes, "set_user_role", lambda user_id, role: None
    )

    response = client.patch(
        "/api/business/users/99/role", json={"role": "owner"}
    )

    assert response.status_code == 404


def test_owner_can_delete_an_employee(monkeypatch):
    log_in_as(FAKE_OWNER)
    monkeypatch.setattr(auth_routes, "delete_employee", lambda user_id: True)

    response = client.delete("/api/business/users/2")

    assert response.status_code == 200


def test_owner_accounts_cannot_be_deleted(monkeypatch):
    log_in_as(FAKE_OWNER)
    monkeypatch.setattr(auth_routes, "delete_employee", lambda user_id: False)

    response = client.delete("/api/business/users/1")

    assert response.status_code == 400


# ---------- Owner approval ----------

PENDING_EMPLOYEE = SimpleNamespace(
    id=3,
    name="Pending Employee",
    email="pending@test.com",
    role="employee",
    status="pending"
)

EMPLOYEE_SIGNUP = {
    "name": "New Employee",
    "email": "new@test.com",
    "password": STRONG_PASSWORD
}


def test_signup_after_the_owner_waits_for_approval(monkeypatch):
    created = []
    monkeypatch.setattr(auth_routes, "count_users", lambda: 1)
    monkeypatch.setattr(auth_routes, "count_pending_users", lambda: 0)
    monkeypatch.setattr(auth_routes, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(
        auth_routes,
        "create_employee_account",
        lambda name, email, password: created.append(email)
    )

    response = client.post("/api/auth/signup", json=EMPLOYEE_SIGNUP)

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert "access_token" not in response.json()
    assert created == ["new@test.com"]


def test_signup_gives_the_same_answer_for_an_existing_email(monkeypatch):
    created = []
    monkeypatch.setattr(auth_routes, "count_users", lambda: 1)
    monkeypatch.setattr(auth_routes, "count_pending_users", lambda: 0)
    monkeypatch.setattr(
        auth_routes, "get_user_by_email", lambda email: FAKE_EMPLOYEE
    )
    monkeypatch.setattr(
        auth_routes,
        "create_employee_account",
        lambda name, email, password: created.append(email)
    )

    response = client.post("/api/auth/signup", json=EMPLOYEE_SIGNUP)

    assert response.status_code == 201
    assert response.json() == auth_routes.PENDING_SIGNUP_RESPONSE
    assert created == []


def test_signup_is_refused_when_too_many_accounts_are_pending(monkeypatch):
    monkeypatch.setattr(auth_routes, "count_users", lambda: 1)
    monkeypatch.setattr(
        auth_routes,
        "count_pending_users",
        lambda: auth_routes.MAX_PENDING_ACCOUNTS
    )

    response = client.post("/api/auth/signup", json=EMPLOYEE_SIGNUP)

    assert response.status_code == 429


def test_pending_user_cannot_log_in(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda email, password: PENDING_EMPLOYEE
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "pending@test.com", "password": STRONG_PASSWORD}
    )

    assert response.status_code == 403
    assert "approval" in response.json()["detail"]


def test_employee_cannot_approve_accounts():
    log_in_as(FAKE_EMPLOYEE)

    response = client.post("/api/business/users/3/approve")

    assert response.status_code == 403


def test_owner_can_approve_a_pending_account(monkeypatch):
    log_in_as(FAKE_OWNER)
    monkeypatch.setattr(
        auth_routes,
        "approve_user",
        lambda user_id: SimpleNamespace(
            **{**vars(PENDING_EMPLOYEE), "status": "active"}
        )
    )

    response = client.post("/api/business/users/3/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


# ---------- Recovery codes ----------

RECOVER_REQUEST = {
    "email": "emp@test.com",
    "recovery_code": "ABCDE-FGH23",
    "new_password": STRONG_PASSWORD
}


def test_login_says_when_recovery_codes_are_needed(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda email, password: FAKE_OWNER
    )
    monkeypatch.setattr(
        auth_routes, "has_unused_recovery_codes", lambda user_id: False
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "owner@test.com", "password": STRONG_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["needs_recovery_codes"] is True


def test_recover_rejects_a_weak_new_password(monkeypatch):
    calls = []
    monkeypatch.setattr(
        auth_routes,
        "reset_password_with_recovery_code",
        lambda email, code, password: calls.append(email)
    )

    response = client.post(
        "/api/auth/recover",
        json={**RECOVER_REQUEST, "new_password": "short"}
    )

    assert response.status_code == 400
    # Rejected before any code was checked.
    assert calls == []


def test_recover_gives_one_answer_for_every_failure(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "reset_password_with_recovery_code",
        lambda email, code, password: False
    )

    response = client.post("/api/auth/recover", json=RECOVER_REQUEST)

    assert response.status_code == 400
    assert response.json()["detail"] == auth_routes.RECOVERY_FAILED_DETAIL


def test_recover_with_a_valid_code(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "reset_password_with_recovery_code",
        lambda email, code, password: True
    )

    response = client.post("/api/auth/recover", json=RECOVER_REQUEST)

    assert response.status_code == 200


def test_employee_cannot_issue_recovery_codes_for_others():
    log_in_as(FAKE_EMPLOYEE)

    response = client.post("/api/business/users/1/recovery-codes")

    assert response.status_code == 403