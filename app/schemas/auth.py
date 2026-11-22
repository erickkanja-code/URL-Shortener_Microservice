"""Business logic for user accounts: registration, login and token refresh."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import AccessToken, LoginRequest, TokenPair
from app.schemas.user import UserCreate


def register_user(db: Session, payload: UserCreate) -> User:
    """Create a new free-tier account and return it.

    The email is stored in lowercase, so "Ann@Example.com" and
    "ann@example.com" count as the same account. Raises 409 if the email
    is already registered. The password is stored only as a hash.
    """
    email = payload.email.lower()

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    return user


def login(db: Session, payload: LoginRequest) -> TokenPair:
    """Check the email and password, and return an access and a refresh token.

    Raises 401 with the same message whether the email is unknown or the
    password is wrong, so the response never reveals which emails have accounts.
    """
    user = db.scalar(select(User).where(User.email == payload.email.lower()))

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


def refresh_access_token(db: Session, refresh_token: str) -> AccessToken:
    """Return a new access token in exchange for a valid refresh token.

    Raises 401 if the token is invalid, expired, not a refresh token, or
    belongs to a user who no longer exists.
    """
    user_id = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)

    if user_id is None or db.get(User, user_id) is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken(access_token=create_access_token(user_id))