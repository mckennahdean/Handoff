import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.database import engine
from backend.models import Business, RecoveryCode, User


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

# Recovery codes: 8 one-time codes like K7QPM-2XH9R. The alphabet
# leaves out look-alike characters (0/O, 1/I/L) so codes are easy
# to copy from paper.
RECOVERY_CODE_COUNT = 8
RECOVERY_CODE_LENGTH = 10
RECOVERY_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

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
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "role": user.role,
        # Issued-at time, compared with password_changed_at so a
        # password reset ends every older session.
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_LIFETIME_HOURS)
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


def record_failed_attempt(user: User, now: datetime):
    """Count a failed login or recovery attempt. The fifth failure
    in a row locks the account for LOCKOUT_MINUTES."""
    user.failed_login_attempts += 1

    if user.failed_login_attempts >= MAX_FAILED_LOGINS:
        user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_login_attempts = 0


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
            record_failed_attempt(user, now)
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


# ---------- Recovery codes ----------

def generate_recovery_code() -> str:
    raw = "".join(
        secrets.choice(RECOVERY_CODE_ALPHABET)
        for _ in range(RECOVERY_CODE_LENGTH)
    )

    return f"{raw[:5]}-{raw[5:]}"


def normalize_recovery_code(code: str) -> str:
    """Accept codes typed casually: any case, with or without
    the dash or spaces."""
    return code.upper().replace("-", "").replace(" ", "").strip()


def create_recovery_codes(user_id: int):
    """Replace a user's recovery codes with a fresh set.

    Returns the plain codes, or None if the user does not exist.
    Only Argon2 hashes are stored: NIST SP 800-63B requires a
    password-hashing scheme for look-up secrets with less than
    112 bits of entropy (these have about 50), so this is the
    only time anyone can see the codes.
    """
    codes = [
        generate_recovery_code()
        for _ in range(RECOVERY_CODE_COUNT)
    ]

    with Session(engine) as session:
        if session.get(User, user_id) is None:
            return None

        session.execute(
            delete(RecoveryCode).where(RecoveryCode.user_id == user_id)
        )

        session.add_all([
            RecoveryCode(
                user_id=user_id,
                code_hash=hash_password(normalize_recovery_code(code))
            )
            for code in codes
        ])

        session.commit()

    return codes


def has_unused_recovery_codes(user_id: int) -> bool:
    with Session(engine) as session:
        remaining = session.scalar(
            select(func.count())
            .select_from(RecoveryCode)
            .where(
                RecoveryCode.user_id == user_id,
                RecoveryCode.used_at.is_(None)
            )
        )

    return remaining > 0


def reset_password_with_recovery_code(
    email: str,
    code: str,
    new_password: str
) -> bool:
    """Set a new password if the code is one of the user's unused
    recovery codes. Each code works once.

    Every attempt checks exactly RECOVERY_CODE_COUNT hashes (real
    ones padded with the dummy hash), so response time does not
    reveal whether the email exists or how many codes are left.
    Wrong codes count toward the same lock as failed logins.
    """
    normalized = normalize_recovery_code(code)

    with Session(engine) as session:
        user = session.scalar(
            select(User).where(User.email == email).with_for_update()
        )

        now = datetime.now(timezone.utc)

        locked = (
            user is not None
            and user.locked_until is not None
            and user.locked_until > now
        )

        if user is None or locked:
            for _ in range(RECOVERY_CODE_COUNT):
                verify_password(normalized, DUMMY_HASH)

            return False

        unused = session.scalars(
            select(RecoveryCode).where(
                RecoveryCode.user_id == user.id,
                RecoveryCode.used_at.is_(None)
            )
        ).all()

        match = None

        for index in range(RECOVERY_CODE_COUNT):
            if index < len(unused):
                if verify_password(normalized, unused[index].code_hash):
                    match = match or unused[index]
            else:
                verify_password(normalized, DUMMY_HASH)

        if match is None:
            record_failed_attempt(user, now)
            session.commit()
            return False

        match.used_at = now
        user.password_hash = hash_password(new_password)
        user.password_changed_at = now
        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()

        return True


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

    # A password reset ends every session that started before it,
    # including one an attacker may have been using. Tokens record
    # whole seconds, so compare in whole seconds.
    issued_at = payload.get("iat")

    if user.password_changed_at is not None and (
        issued_at is None
        or issued_at < int(user.password_changed_at.timestamp())
    ):
        raise HTTPException(
            status_code=401,
            detail="Your password was changed. Please log in again."
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


def unlock_user(user_id: int):
    """Clear failed attempts and any lock. Returns True, or None
    if the user does not exist."""
    with Session(engine) as session:
        user = session.get(User, user_id)

        if user is None:
            return None

        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()

        return True


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