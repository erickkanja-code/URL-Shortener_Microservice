import ipaddress
import secrets
import string
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..managers import URLManager
from ..models import URL, Click, Tag, User

router = APIRouter(prefix="/api/v1/urls", tags=["URLs"])
redirect_router = APIRouter(tags=["Redirect"])

SessionDep = Annotated[Session, Depends(get_db)]

ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 7


# ---------- Request schemas (what the API accepts) ----------

class URLCreate(BaseModel):
    original_url: HttpUrl
    owner_id: int
    custom_alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,10}$")
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    tags: list[str] = []


class URLUpdate(BaseModel):
    owner_id: int
    original_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    is_active: bool | None = None
    tags: list[str] | None = None


# ---------- Response schemas (what the API returns) ----------

class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class OwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class URLResponse(BaseModel):
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
    items: list[URLResponse]
    total: int
    page: int
    size: int


# ---------- Helpers ----------

def generate_short_code(db: Session) -> str:
    while True:
        short_code = "".join(secrets.choice(ALPHABET) for _ in range(SHORT_CODE_LENGTH))
        existing_url = db.scalar(select(URL).where(URL.short_code == short_code))
        if existing_url is None:
            return short_code


def get_tags(db: Session, names: list[str]) -> list[Tag]:
    if not names:
        return []
    tags = db.scalars(select(Tag).where(Tag.name.in_(names))).all()
    missing = set(names) - {tag.name for tag in tags}
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown tags: {', '.join(sorted(missing))}")
    return list(tags)


def get_owned_url(db: Session, short_code: str, owner_id: int) -> URL:
    query = URLManager.with_owner_and_tags(
        select(URL).where(URL.short_code == short_code, URL.owner_id == owner_id)
    )
    url = db.scalar(query)
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


def get_client_ip(request: Request) -> str:
    host = request.client.host if request.client else ""
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        return "0.0.0.0"


# ---------- URL operations ----------

@router.post("/", status_code=201, response_model=URLResponse)
def create_url(payload: URLCreate, db: SessionDep):
    if db.get(User, payload.owner_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    original_url = str(payload.original_url)
    duplicate = db.scalar(
        select(URL).where(URL.original_url == original_url, URL.owner_id == payload.owner_id)
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This URL has already been shortened")

    if payload.custom_alias:
        alias_taken = db.scalar(select(URL).where(URL.short_code == payload.custom_alias))
        if alias_taken:
            raise HTTPException(status_code=409, detail="This alias is already taken")
        short_code = payload.custom_alias
    else:
        short_code = generate_short_code(db)

    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        custom_alias=payload.custom_alias,
        owner_id=payload.owner_id,
        title=payload.title,
        description=payload.description,
        expires_at=payload.expires_at,
        tags=get_tags(db, payload.tags),
    )
    db.add(new_url)
    db.commit()
    return new_url


@router.get("/", response_model=URLListResponse)
def list_urls(
    db: SessionDep,
    owner_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    total = db.scalar(select(func.count()).select_from(URL).where(URL.owner_id == owner_id))

    query = URLManager.with_owner_and_tags(
        select(URL)
        .where(URL.owner_id == owner_id)
        .order_by(URL.created_at.desc(), URL.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    urls = db.scalars(query).all()

    return {"items": urls, "total": total, "page": page, "size": size}


@router.get("/{short_code}/", response_model=URLResponse)
def get_url(short_code: str, owner_id: int, db: SessionDep):
    return get_owned_url(db, short_code, owner_id)


@router.put("/{short_code}/", response_model=URLResponse)
def update_url(short_code: str, payload: URLUpdate, db: SessionDep):
    url = get_owned_url(db, short_code, payload.owner_id)

    changes = payload.model_dump(exclude_unset=True, exclude={"owner_id", "tags"})
    for field, value in changes.items():
        setattr(url, field, value)
    if "original_url" in changes:
        url.original_url = str(payload.original_url)

    if payload.tags is not None:
        url.tags = get_tags(db, payload.tags)

    db.commit()
    return url


@router.delete("/{short_code}/", status_code=204)
def delete_url(short_code: str, owner_id: int, db: SessionDep):
    url = get_owned_url(db, short_code, owner_id)
    url.is_active = False
    db.commit()


# ---------- Public redirect ----------

@redirect_router.get("/{short_code}/")
def redirect_to_original(short_code: str, request: Request, db: SessionDep):
    url = db.scalar(URLManager.active_urls().where(URL.short_code == short_code))
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    db.add(
        Click(
            url_id=url.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            referrer=request.headers.get("referer"),
        )
    )
    db.execute(
        update(URL).where(URL.id == url.id).values(click_count=URL.click_count + 1)
    )
    original_url = url.original_url
    db.commit()

    return RedirectResponse(url=original_url, status_code=302)