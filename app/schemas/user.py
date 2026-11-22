"""Schemas for registering users and returning user data."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Tier


class UserCreate(BaseModel):
    """Request body for registering a new account."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """A user as returned by the API. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    tier: Tier
    is_premium: bool


class OwnerResponse(BaseModel):
    """The owner of a URL, as shown inside URL responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str