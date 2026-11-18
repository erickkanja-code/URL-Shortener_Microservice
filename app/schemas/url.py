"""Schemas for creating, updating and returning URLs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.tag import TagResponse
from app.schemas.user import OwnerResponse


class URLCreate(BaseModel):
    """Request body for creating a short URL."""

    original_url: HttpUrl
    owner_id: int
    custom_alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,10}$")
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    tags: list[str] = []


class URLUpdate(BaseModel):
    """Request body for updating a URL.

    `owner_id` identifies who is making the request. Every other field is
    optional, and only the fields actually sent are changed.
    """

    owner_id: int
    original_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    is_active: bool | None = None
    tags: list[str] | None = None


class URLResponse(BaseModel):
    """A URL as returned by the API, with its owner and tags."""

    model_config = ConfigDict(from_attributes=True)

    short_code: str
    original_url: str
    custom_alias: str | None
    is_active: bool
    expires_at: datetime | None
    title: str | None
    description: str | None
    favicon: str | None
    click_count: int
    created_at: datetime
    owner: OwnerResponse
    tags: list[TagResponse]


class URLListResponse(BaseModel):
    """One page of a user's URLs, with the information needed to paginate."""

    items: list[URLResponse]
    total: int
    page: int
    size: int