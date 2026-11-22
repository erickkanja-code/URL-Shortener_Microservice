"""Business logic for user accounts: registration (and, later, login)."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
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