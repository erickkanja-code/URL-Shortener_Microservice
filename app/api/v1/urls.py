"""Endpoints for managing short URLs, under /api/v1/urls.

Every endpoint requires a valid access token. Each endpoint only handles
HTTP concerns (parameters, status codes and response models) and delegates
the work, including permission checks, to `app.services.url`.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, SessionDep
from app.schemas.url import URLCreate, URLListResponse, URLResponse, URLUpdate
from app.services import url as url_service

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", status_code=201, response_model=URLResponse)
def create_url(payload: URLCreate, db: SessionDep, current_user: CurrentUserDep):
    """Create a short URL owned by the logged-in user."""
    return url_service.create_url(db, payload, current_user)


@router.get("/", response_model=URLListResponse)
def list_urls(
    db: SessionDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    """List one page of the logged-in user's URLs, newest first."""
    urls, total = url_service.list_urls(db, current_user, page, size)
    return {"items": urls, "total": total, "page": page, "size": size}


@router.get("/{short_code}/", response_model=URLResponse)
def get_url(short_code: str, db: SessionDep, current_user: CurrentUserDep):
    """Return the details of a URL. Any logged-in user may read any URL."""
    return url_service.get_url(db, short_code)


@router.put("/{short_code}/", response_model=URLResponse)
def update_url(short_code: str, payload: URLUpdate, db: SessionDep, current_user: CurrentUserDep):
    """Update the fields sent in the request body. Only the owner may do this."""
    return url_service.update_url(db, short_code, payload, current_user)


@router.delete("/{short_code}/", status_code=204)
def delete_url(short_code: str, db: SessionDep, current_user: CurrentUserDep):
    """Deactivate a URL, keeping its click history. Only the owner may do this."""
    url_service.deactivate_url(db, short_code, current_user)