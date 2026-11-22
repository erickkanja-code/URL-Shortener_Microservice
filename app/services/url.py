"""Business logic for short URLs.

These functions hold the rules of the app (duplicates are rejected, an
alias becomes the short code, deleting means deactivating, and so on).
They know nothing about URL paths or request objects; the API layer calls
them with plain values and the logged-in user.

Permissions follow the IsOwnerOrReadOnly rule: any logged-in user may read
a URL's details, but only its owner may change or deactivate it. Tier rules
(the active URL limit and custom aliases) come from `app.services.tiers`.

They raise `HTTPException` directly. This is a deliberate simplification:
a stricter design would raise custom exceptions and let the API layer turn
them into HTTP responses.
"""

import secrets
import string

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.managers.url import URLManager
from app.models import URL, Click, Tag, User
from app.schemas.url import URLCreate, URLUpdate
from app.services.tiers import ensure_can_use_custom_alias, ensure_within_active_url_limit

ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 7


def generate_short_code(db: Session) -> str:
    """Return a random 7-character code that no URL is using yet."""
    while True:
        short_code = "".join(secrets.choice(ALPHABET) for _ in range(SHORT_CODE_LENGTH))
        existing_url = db.scalar(select(URL).where(URL.short_code == short_code))
        if existing_url is None:
            return short_code


def get_tags(db: Session, names: list[str]) -> list[Tag]:
    """Return the Tag rows for the given names.

    Raises 400 if any name does not match an existing tag.
    """
    if not names:
        return []
    tags = db.scalars(select(Tag).where(Tag.name.in_(names))).all()
    missing = set(names) - {tag.name for tag in tags}
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown tags: {', '.join(sorted(missing))}")
    return list(tags)


def get_url(db: Session, short_code: str) -> URL:
    """Return the URL with this short code, with its owner and tags loaded.

    Any logged-in user may read any URL (the "ReadOnly" part of
    IsOwnerOrReadOnly). Raises 404 if the short code does not exist.
    """
    query = URLManager.with_owner_and_tags(select(URL).where(URL.short_code == short_code))
    url = db.scalar(query)
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


def ensure_owner(url: URL, user: User) -> None:
    """Raise 403 unless the user owns the URL (the "IsOwner" part of IsOwnerOrReadOnly)."""
    if url.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own this URL")


def create_url(db: Session, payload: URLCreate, owner: User) -> URL:
    """Create and save a short URL owned by the given user.

    Raises 409 if this owner already shortened this URL or the alias is
    taken, 400 for unknown tags, and 403 if a Free user asks for a custom
    alias or would go over the active URL limit. A custom alias, when
    given, becomes the short code.
    """
    original_url = str(payload.original_url)
    duplicate = db.scalar(
        select(URL).where(URL.original_url == original_url, URL.owner_id == owner.id)
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This URL has already been shortened")

    if payload.custom_alias:
        ensure_can_use_custom_alias(owner)
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
        owner_id=owner.id,
        title=payload.title,
        description=payload.description,
        expires_at=payload.expires_at,
        tags=get_tags(db, payload.tags),
    )
    db.add(new_url)
    db.flush()
    ensure_within_active_url_limit(db, owner)
    db.commit()
    return new_url


def list_urls(db: Session, owner: User, page: int, size: int) -> tuple[list[URL], int]:
    """Return one page of the owner's URLs, newest first, and their total count.

    Pages are numbered from 1. URLs created at the same moment are ordered
    by id, so pages never overlap or skip rows.
    """
    total = db.scalar(select(func.count()).select_from(URL).where(URL.owner_id == owner.id))

    query = URLManager.with_owner_and_tags(
        select(URL)
        .where(URL.owner_id == owner.id)
        .order_by(URL.created_at.desc(), URL.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    urls = list(db.scalars(query).all())

    return urls, total


def update_url(db: Session, short_code: str, payload: URLUpdate, user: User) -> URL:
    """Update only the fields the client sent, and return the updated URL.

    Raises 404 if the short code does not exist, 403 if the user does not
    own the URL or a Free user would go over the active URL limit (by
    reactivating a URL or extending its expiry), and 400 for unknown tags.
    Sending `tags` replaces the URL's tags.
    """
    url = get_url(db, short_code)
    ensure_owner(url, user)

    changes = payload.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in changes.items():
        setattr(url, field, value)
    if "original_url" in changes:
        url.original_url = str(payload.original_url)

    if payload.tags is not None:
        url.tags = get_tags(db, payload.tags)

    if "is_active" in changes or "expires_at" in changes:
        db.flush()
        ensure_within_active_url_limit(db, user)

    db.commit()
    return url


def deactivate_url(db: Session, short_code: str, user: User) -> None:
    """Deactivate a URL instead of deleting it, keeping its click history.

    Raises 404 if the short code does not exist, and 403 if the user does
    not own the URL.
    """
    url = get_url(db, short_code)
    ensure_owner(url, user)
    url.is_active = False
    db.commit()


def resolve_short_code(
    db: Session,
    short_code: str,
    ip_address: str,
    user_agent: str,
    referrer: str | None,
) -> str:
    """Record a visit to a short code and return the URL to redirect to.

    Only active, non-expired URLs resolve; anything else raises 404. The
    click is saved and `click_count` is incremented in the same transaction.
    The increment runs in SQL, so simultaneous clicks are never lost.
    """
    url = db.scalar(URLManager.active_urls().where(URL.short_code == short_code))
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    db.add(
        Click(
            url_id=url.id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )
    )
    db.execute(update(URL).where(URL.id == url.id).values(click_count=URL.click_count + 1))
    original_url = url.original_url
    db.commit()

    return original_url