import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Business, User


load_dotenv()

ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 8
INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
INVITE_CODE_LENGTH = 8

password_hasher = PasswordHash.recommended()

# Checked against when an email does not exist, so a failed login
# takes the same time either way. This prevents attackers from
# discovering which emails have accounts by measuring response time.
DUMMY_HASH = password_hasher.hash("dummy-password-for-timing")

bearer_scheme = HTTPBearer(auto_error=False)


def get_secret_key():
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    return secret


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


# ---------- Tokens ----------

def create_access_token(user: User) -> str:
    expires = (
        datetime.now(timezone.utc)
        + timedelta(hours=TOKEN_LIFETIME_HOURS)
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expires
    }

    return jwt.encode(
        payload,
        get_secret_key(),
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        get_secret_key(),
        algorithms=[ALGORITHM]
    )


# ---------- Invite codes ----------

def generate_invite_code() -> str:
    return "".join(
        secrets.choice(INVITE_CODE_ALPHABET)
        for _ in range(INVITE_CODE_LENGTH)
    )


def get_business():
    with Session(engine) as session:
        return session.scalar(
            select(Business).limit(1)
        )


def invite_code_is_valid(code: str) -> bool:
    business = get_business()

    if business is None:
        return False

    return secrets.compare_digest(
        business.invite_code.encode(),
        code.strip().upper().encode()
    )


def regenerate_invite_code() -> str:
    with Session(engine) as session:
        business = session.scalar(
            select(Business).limit(1)
        )

        business.invite_code = generate_invite_code()
        session.commit()

        return business.invite_code


# ---------- Users ----------

def count_users() -> int:
    with Session(engine) as session:
        return session.scalar(
            select(func.count()).select_from(User)
        )


def get_user_by_email(email: str):
    with Session(engine) as session:
        return session.scalar(
            select(User).where(User.email == email)
        )


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)

    if user is None:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_owner_account(
    name: str,
    email: str,
    password: str,
    business_name: str
):
    with Session(engine) as session:
        business = Business(
            name=business_name,
            invite_code=generate_invite_code()
        )

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="owner"
        )

        session.add_all([business, user])
        session.commit()
        session.refresh(user)

        return user


def create_employee_account(
    name: str,
    email: str,
    password: str
):
    with Session(engine) as session:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="employee"
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


# ---------- FastAPI dependencies ----------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated."
        )

    try:
        payload = decode_access_token(
            credentials.credentials
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Session expired. Please log in again."
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )

    with Session(engine) as session:
        user = session.get(User, int(payload["sub"]))

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists."
        )

    return user


def require_owner(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Owner access required."
        )

    return user