from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from backend.auth_service import (
    MAX_PENDING_ACCOUNTS,
    approve_user,
    authenticate_user,
    count_pending_users,
    count_users,
    create_access_token,
    create_employee_account,
    create_owner_account,
    create_recovery_codes,
    delete_employee,
    get_current_user,
    get_user_by_email,
    has_unused_recovery_codes,
    hash_password,
    list_users,
    password_problems,
    require_owner,
    reset_password_with_recovery_code,
    set_user_role,
)

from backend.models import User


router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    business_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str

class UserRoleUpdate(BaseModel):
    role: str


class RecoverRequest(BaseModel):
    email: str
    recovery_code: str
    new_password: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user.status
    }


def auth_response(user: User) -> dict:
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user_to_dict(user),
        # True on a first sign-in (or after every code was used):
        # the app then shows a fresh set of recovery codes once.
        "needs_recovery_codes": not has_unused_recovery_codes(user.id)
    }


@router.get("/api/auth/setup-status")
def setup_status():
    return {
        "needs_owner": count_users() == 0
    }


PENDING_SIGNUP_RESPONSE = {
    "status": "pending",
    "message": (
        "Account created. Your business owner needs to approve it "
        "before you can sign in."
    )
}


@router.post("/api/auth/signup", status_code=201)
def signup(request: SignupRequest):
    name = request.name.strip()
    email = normalize_email(request.email)

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required."
        )

    if "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="A valid email address is required."
        )

    problems = password_problems(request.password)

    if problems:
        raise HTTPException(
            status_code=400,
            detail="Password must contain " + ", ".join(problems) + "."
        )

    # The first account creates the business and becomes its owner.
    if count_users() == 0:
        business_name = (request.business_name or "").strip()

        if not business_name:
            raise HTTPException(
                status_code=400,
                detail="Business name is required for the owner account."
            )

        try:
            user = create_owner_account(
                name,
                email,
                request.password,
                business_name
            )
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists."
            )

        return auth_response(user)

    # Everyone after that joins as a pending employee, with no
    # login token until an owner approves the account.
    if count_pending_users() >= MAX_PENDING_ACCOUNTS:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many pending requests. "
                "Please contact your business owner."
            )
        )

    # Same answer, and the same hashing work, whether or not the
    # email already has an account, so signup cannot be used to
    # discover which emails are registered.
    if get_user_by_email(email) is None:
        try:
            create_employee_account(name, email, request.password)
        except IntegrityError:
            pass
    else:
        hash_password(request.password)

    return PENDING_SIGNUP_RESPONSE


@router.post("/api/auth/login")
def login(request: LoginRequest):
    user = authenticate_user(
        normalize_email(request.email),
        request.password
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password. After 5 failed attempts, "
                "sign-in is paused for 15 minutes."
            )
        )

    # Only reachable with the correct password, so it reveals
    # nothing to someone guessing emails.
    if user.status != "active":
        raise HTTPException(
            status_code=403,
            detail="Your account is waiting for owner approval."
        )

    return auth_response(user)


@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)


# ---------- Recovery codes ----------

RECOVERY_FAILED_DETAIL = (
    "That email and recovery code do not match, or the code was "
    "already used. After 5 failed attempts, recovery is paused "
    "for 15 minutes."
)


@router.post("/api/auth/recovery-codes")
def new_recovery_codes(user: User = Depends(get_current_user)):
    """Replace your own recovery codes. Shown once."""
    return {"codes": create_recovery_codes(user.id)}


@router.post("/api/auth/recover")
def recover_account(request: RecoverRequest):
    # Checking the new password first reveals nothing about
    # whether the email or code is valid.
    problems = password_problems(request.new_password)

    if problems:
        raise HTTPException(
            status_code=400,
            detail="Password must contain " + ", ".join(problems) + "."
        )

    reset = reset_password_with_recovery_code(
        normalize_email(request.email),
        request.recovery_code,
        request.new_password
    )

    if not reset:
        raise HTTPException(
            status_code=400,
            detail=RECOVERY_FAILED_DETAIL
        )

    return {"message": "Password updated. You can now sign in."}


# ---------- User management (owner only) ----------

@router.get(
    "/api/business/users",
    dependencies=[Depends(require_owner)]
)
def get_users():
    return [user_to_dict(user) for user in list_users()]


@router.post(
    "/api/business/users/{user_id}/approve",
    dependencies=[Depends(require_owner)]
)
def approve_pending_user(user_id: int):
    user = approve_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return user_to_dict(user)


@router.post(
    "/api/business/users/{user_id}/recovery-codes",
    dependencies=[Depends(require_owner)]
)
def issue_recovery_codes(user_id: int):
    """An owner issues a fresh set for someone who lost theirs.
    The old set stops working immediately."""
    codes = create_recovery_codes(user_id)

    if codes is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return {"codes": codes}


@router.patch("/api/business/users/{user_id}/role")
def update_user_role(
    user_id: int,
    request: UserRoleUpdate,
    owner: User = Depends(require_owner)
):
    if request.role not in {"owner", "employee"}:
        raise HTTPException(
            status_code=400,
            detail="Role must be owner or employee."
        )

    # The page disables your own role, but the server enforces it.
    # Whoever changes a role stays an owner, so the business always
    # keeps at least one owner.
    if user_id == owner.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role."
        )

    user = set_user_role(user_id, request.role)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    return user_to_dict(user)


@router.delete(
    "/api/business/users/{user_id}",
    dependencies=[Depends(require_owner)]
)
def delete_user(user_id: int):
    deleted = delete_employee(user_id)

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    if not deleted:
        raise HTTPException(
            status_code=400,
            detail="Only employee accounts can be deleted."
        )

    return {
        "message": "Employee account deleted."
    }