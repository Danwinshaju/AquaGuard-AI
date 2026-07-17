"""Password hashing, login sessions, and current-user dependencies."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, HTTPException, Response, status
from starlette.requests import HTTPConnection

from app.core.config import get_settings
from app.db.repositories.auth import auth_repository
from app.models import UserDocument

SESSION_COOKIE = "aquaguard_session"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SESSION_DAYS = 7


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=64,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


# Used to keep failed-login password work similar when an email is not registered.
DUMMY_PASSWORD_HASH = hash_password("aquaguard-dummy-password")


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, expected_hex = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(expected_hex)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual.hex(), expected_hex)


def session_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


async def create_account_session(response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
    await auth_repository.create_session(
        token_hash=session_token_hash(token),
        user_id=user_id,
        expires_at=expires_at,
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        expires=expires_at,
        path="/",
        secure=get_settings().app_env.lower() == "production",
        httponly=True,
        samesite="lax",
    )


async def get_current_user(connection: HTTPConnection) -> UserDocument:
    token = connection.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in.")
    user = await auth_repository.user_for_session(session_token_hash(token))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
        )
    return user


CurrentUser = Annotated[UserDocument, Depends(get_current_user)]


def new_user(name: str, email: str, password: str) -> UserDocument:
    return UserDocument(
        id=str(uuid4()),
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
