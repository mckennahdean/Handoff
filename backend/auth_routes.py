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
    regenerate_invite_code,
    require_owner,
)
from backend.models import User


router = APIRouter()

MIN_PASSWORD_LENGTH = 8


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    business_name: Optional[str] = None
    invite_code: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


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

    if len(request.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters."
            )
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
            detail="Invalid email or password."
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