"""Schemas for logging in and refreshing tokens."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request body for logging in."""

    email: EmailStr
    password: str = Field(max_length=128)


class TokenPair(BaseModel):
    """The tokens returned by a successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request body for getting a new access token."""

    refresh_token: str


class AccessToken(BaseModel):
    """A new access token, returned by the refresh endpoint."""

    access_token: str
    token_type: str = "bearer"