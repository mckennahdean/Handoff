import os
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

# Login throttling. NIST SP 800-63B requires limiting failed
# attempts; a temporary lock (not a permanent one) stops password
# guessing without letting an attacker lock someone out for good.
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15

# Signups wait for owner approval; cap the queue so it cannot be flooded.
MAX_PENDING_ACCOUNTS = 20

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

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


def password_problems(password: str) -> list[str]:
    """Return a list of unmet password rules (empty means valid).

    Policy follows PCI DSS v4.0 guidance: minimum 12 characters,
    plus mixed character types. The maximum prevents oversized
    inputs from consuming excessive CPU during Argon2 hashing.
    """
    problems = []

    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"at least {MIN_PASSWORD_LENGTH} characters")

    if len(password) > MAX_PASSWORD_LENGTH:
        problems.append(f"no more than {MAX_PASSWORD_LENGTH} characters")

    if not any(char.isupper() for char in password):
        problems.append("an uppercase letter")

    if not any(char.islower() for char in password):
        problems.append("a lowercase letter")

    if not any(char.isdigit() for char in password):
        problems.append("a number")

    if not any(not char.isalnum() for char in password):
        problems.append("a special character")

    return problems


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


# ---------- Business ----------

def get_business():
    with Session(engine) as session:
        return session.scalar(
            select(Business).limit(1)
        )


# ---------- Users ----------

def count_users() -> int:
    with Session(engine) as session:
        return session.scalar(
            select(func.count()).select_from(User)
        )


def count_pending_users() -> int:
    with Session(engine) as session:
        return session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.status == "pending")
        )


def get_user_by_email(email: str):
    with Session(engine) as session:
        return session.scalar(
            select(User).where(User.email == email)
        )


def authenticate_user(email: str, password: str):
    with Session(engine) as session:
        # FOR UPDATE locks this user's row until commit, so two
        # simultaneous attempts cannot both miss a failure.
        user = session.scalar(
            select(User).where(User.email == email).with_for_update()
        )

        if user is None:
            verify_password(password, DUMMY_HASH)
            return None

        now = datetime.now(timezone.utc)

        if user.locked_until is not None and user.locked_until > now:
            # Same work as a normal attempt, so response timing
            # does not reveal that the account is locked.
            verify_password(password, DUMMY_HASH)
            return None

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(
                    minutes=LOCKOUT_MINUTES
                )
                user.failed_login_attempts = 0

            session.commit()
            return None

        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()
        session.refresh(user)

        return user


def create_owner_account(
    name: str,
    email: str,
    password: str,
    business_name: str
):
    with Session(engine) as session:
        business = Business(
            name=business_name
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
            role="employee",
            status="pending"
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

    # Defense in depth: pending accounts never receive a token,
    # but if one somehow had a token, it still would not work.
    if user.status != "active":
        raise HTTPException(
            status_code=403,
            detail="Your account is waiting for owner approval."
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



# ---------- User management ----------

def list_users() -> list:
    with Session(engine) as session:
        return session.scalars(
            select(User).order_by(User.name)
        ).all()


def approve_user(user_id: int):
    """Activate a pending account. Returns the user,
    or None if the user does not exist."""
    with Session(engine) as session:
        user = session.get(User, user_id)

        if user is None:
            return None

        user.status = "active"
        session.commit()
        session.refresh(user)

        return user


def set_user_role(user_id: int, role: str):
    """Change a user's role. Returns the updated user,
    or None if the user does not exist."""
    with Session(engine) as session:
        user = session.get(User, user_id)

        if user is None:
            return None

        user.role = role
        session.commit()
        session.refresh(user)

        return user


def delete_employee(user_id: int):
    """Delete an employee account. Returns True when deleted,
    False when the account is an owner (owners are never
    deleted), or None if the user does not exist."""
    with Session(engine) as session:
        user = session.get(User, user_id)

        if user is None:
            return None

        if user.role != "employee":
            return False

        session.delete(user)
        session.commit()

        return True
