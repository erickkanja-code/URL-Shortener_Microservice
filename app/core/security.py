"""Password hashing and JWT creation and verification.

Passwords are never stored. Only an Argon2 hash of each password is kept,
which cannot be turned back into the password. To check a login, the
password the user typed is hashed again and compared with the stored hash.

Tokens are JWTs signed with JWT_SECRET_KEY. Their payload can be read by
anyone, but cannot be changed without invalidating the signature. Each
token carries the user's id (`sub`), an expiry time (`exp`) and its type
("access" or "refresh"), so one kind can never be used as the other.
"""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

password_hash = PasswordHash.recommended()


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    """Return an Argon2 hash of the password, safe to store in the database."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if the password matches the stored hash."""
    return password_hash.verify(password, hashed_password)


# ---------- Tokens ----------

def create_token(user_id: int, token_type: str, expires_in: timedelta) -> str:
    """Return a signed JWT for the user, of the given type, expiring after `expires_in`."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    """Return a short-lived access token, sent with every authenticated request."""
    return create_token(user_id, ACCESS_TOKEN_TYPE, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    """Return a long-lived refresh token, used only to get new access tokens."""
    return create_token(user_id, REFRESH_TOKEN_TYPE, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> int | None:
    """Return the user id from a valid token of the expected type, or None.

    A token is rejected (None) if its signature is wrong, it has expired,
    it is malformed, or it is the wrong type of token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None

    if payload.get("type") != expected_type:
        return None
    return int(payload["sub"])