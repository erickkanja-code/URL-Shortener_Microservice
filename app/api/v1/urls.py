"""Endpoints for managing short URLs, under /api/v1/urls.

Each endpoint only handles HTTP concerns (parameters, status codes and
response models) and delegates the work to `app.services.url`.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.url import URLCreate, URLListResponse, URLResponse, URLUpdate
from app.services import url as url_service

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", status_code=201, response_model=URLResponse)
def create_url(payload: URLCreate, db: SessionDep):
    """Create a short URL for the given owner."""
    return url_service.create_url(db, payload)


@router.get("/", response_model=URLListResponse)
def list_urls(
    db: SessionDep,
    owner_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    """List one page of an owner's URLs, newest first."""
    urls, total = url_service.list_urls(db, owner_id, page, size)
    return {"items": urls, "total": total, "page": page, "size": size}


@router.get("/{short_code}/", response_model=URLResponse)
def get_url(short_code: str, owner_id: int, db: SessionDep):
    """Return the details of one of the owner's URLs."""
    return url_service.get_owned_url(db, short_code, owner_id)


@router.put("/{short_code}/", response_model=URLResponse)
def update_url(short_code: str, payload: URLUpdate, db: SessionDep):
    """Update the fields sent in the request body."""
    return url_service.update_url(db, short_code, payload)


@router.delete("/{short_code}/", status_code=204)
def delete_url(short_code: str, owner_id: int, db: SessionDep):
    """Deactivate a URL. Its click history is kept."""
    url_service.deactivate_url(db, short_code, owner_id)