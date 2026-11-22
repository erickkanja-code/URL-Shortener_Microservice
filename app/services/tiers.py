"""Tier rules: what Free and Premium users may do.

| Feature            | Free           | Premium   |
|--------------------|----------------|-----------|
| Active URLs        | max 10         | unlimited |
| Custom aliases     | not allowed    | allowed   |
| Detailed analytics | not allowed    | allowed   |

Admins get Premium access. The user's `tier` is the source of truth for
these rules.
"""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.managers.url import URLManager
from app.models import URL, Tier, User

FREE_ACTIVE_URL_LIMIT = 10


def has_premium_access(user: User) -> bool:
    """Return True if the user's tier unlocks Premium features."""
    return user.tier in (Tier.PREMIUM, Tier.ADMIN)


def count_active_urls(db: Session, user: User) -> int:
    """Return how many of the user's URLs are active and not expired."""
    active_urls = URLManager.active_urls().where(URL.owner_id == user.id).subquery()
    return db.scalar(select(func.count()).select_from(active_urls))


def ensure_within_active_url_limit(db: Session, user: User) -> None:
    """Raise 403 if a Free user now has more active URLs than allowed.

    Call this after adding or changing a URL and flushing, but before
    committing: the count then includes the pending change. If the limit
    is exceeded, the change is rolled back.
    """
    if has_premium_access(user):
        return
    if count_active_urls(db, user) > FREE_ACTIVE_URL_LIMIT:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail=f"Free accounts can have at most {FREE_ACTIVE_URL_LIMIT} active URLs. "
            "Upgrade to Premium for unlimited URLs.",
        )


def ensure_can_use_custom_alias(user: User) -> None:
    """Raise 403 if the user is not allowed to choose a custom alias."""
    if not has_premium_access(user):
        raise HTTPException(status_code=403, detail="Custom aliases are a Premium feature")


def ensure_can_view_analytics(user: User) -> None:
    """Raise 403 if the user is not allowed to see detailed analytics."""
    if not has_premium_access(user):
        raise HTTPException(status_code=403, detail="Detailed analytics are a Premium feature")