from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from backend.auth_service import (
    authenticate_user,
    count_users,
    create_access_token,
    create_employee_account,
    create_owner_account,
    get_business,
    get_current_user,
    get_user_by_email,
    invite_code_is_valid,
    password_problems,
    regenerate_invite_code,
    require_owner,    
    delete_employee,
    list_users,
    set_user_role,
)

from backend.models import User


router = APIRouter()


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    business_name: Optional[str] = None
    invite_code: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str

class UserRoleUpdate(BaseModel):
    role: str

def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


def auth_response(user: User) -> dict:
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user_to_dict(user)
    }


@router.get("/api/auth/setup-status")
def setup_status():
    return {
        "needs_owner": count_users() == 0
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

    is_first_account = count_users() == 0

    # Check the invite code BEFORE checking for duplicate emails,
    # so someone without a valid code cannot probe which emails
    # already have accounts.

    if is_first_account:
        business_name = (request.business_name or "").strip()

        if not business_name:
            raise HTTPException(
                status_code=400,
                detail="Business name is required for the owner account."
            )

    else:
        if (
            not request.invite_code
            or not invite_code_is_valid(request.invite_code)
        ):
            raise HTTPException(
                status_code=403,
                detail="Invalid invite code."
            )

    if get_user_by_email(email) is not None:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    try:
        if is_first_account:
            user = create_owner_account(
                name,
                email,
                request.password,
                business_name
            )

        else:
            user = create_employee_account(
                name,
                email,
                request.password
            )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    return auth_response(user)


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

    return auth_response(user)


@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)


@router.get(
    "/api/business/invite-code",
    dependencies=[Depends(require_owner)]
)
def get_invite_code():
    business = get_business()

    return {
        "business_name": business.name,
        "invite_code": business.invite_code
    }


@router.post(
    "/api/business/invite-code/regenerate",
    dependencies=[Depends(require_owner)]
)
def new_invite_code():
    return {
        "invite_code": regenerate_invite_code()
    }


# ---------- User management (owner only) ----------

@router.get(
    "/api/business/users",
    dependencies=[Depends(require_owner)]
)
def get_users():
    return [user_to_dict(user) for user in list_users()]


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
    