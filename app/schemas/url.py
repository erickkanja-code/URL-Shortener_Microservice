"""Schemas for creating, updating and returning URLs.

Every URL submitted to the API passes through `SafeHttpUrl`, which
sanitizes it before any business logic runs. Text fields have surrounding
whitespace stripped.
"""

import ipaddress
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.tag import TagResponse
from app.schemas.user import OwnerResponse

MAX_URL_LENGTH = 2048  # matches the size of the original_url column


def check_url_is_safe(url: HttpUrl) -> HttpUrl:
    """Reject URLs that are too long, contain credentials, or point to private networks.

    By the time this runs, HttpUrl has already trimmed whitespace, normalized
    the URL and rejected every scheme except http and https (so values like
    "javascript:..." never get here). A ValueError becomes a 422 response.
    """
    if len(str(url)) > MAX_URL_LENGTH:
        raise ValueError(f"URL must be at most {MAX_URL_LENGTH} characters")

    if url.username or url.password:
        raise ValueError("URL must not contain a username or password")

    host = (url.host or "").strip("[]")  # IPv6 hosts come wrapped in brackets
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("URL must not point to localhost")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return url  # a domain name, not an IP address

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
        raise ValueError("URL must not point to a private or local network address")
    return url


SafeHttpUrl = Annotated[HttpUrl, AfterValidator(check_url_is_safe)]
"""An http(s) URL that has been sanitized by `check_url_is_safe`."""


class URLCreate(BaseModel):
    """Request body for creating a short URL.

    The owner is always the logged-in user, taken from the access token.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    original_url: SafeHttpUrl
    custom_alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,10}$")
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    tags: list[str] = []


class URLUpdate(BaseModel):
    """Request body for updating a URL.

    Every field is optional, and only the fields actually sent are changed.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    original_url: SafeHttpUrl | None = None
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