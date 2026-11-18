"""Reusable queries for URLs.

Each method returns a `Select` query rather than results, so callers can
refine it further (filter, order, paginate) before running it, much like
a Django QuerySet.
"""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from app.models import URL


class URLManager:
    """Query builders for the URL model."""

    @staticmethod
    def active_urls() -> Select:
        """Return a query for URLs that are active and not expired.

        A URL with no `expires_at` never expires.
        """
        return select(URL).where(
            URL.is_active.is_(True),
            or_(URL.expires_at.is_(None), URL.expires_at > func.now()),
        )

    @staticmethod
    def expired_urls() -> Select:
        """Return a query for URLs whose `expires_at` is in the past."""
        return select(URL).where(URL.expires_at <= func.now())

    @staticmethod
    def popular_urls() -> Select:
        """Return a query for all URLs, ordered from most to fewest clicks."""
        return select(URL).order_by(URL.click_count.desc())

    @staticmethod
    def with_owner_and_tags(query: Select) -> Select:
        """Add eager loading of each URL's owner and tags to a query.

        This prevents the N+1 problem when the caller will use `url.owner`
        or `url.tags`:

        - `joinedload` fetches the owner in the same query with a JOIN
          (the equivalent of Django's `select_related`).
        - `selectinload` fetches the tags in one extra query using IN
          (the equivalent of Django's `prefetch_related`).
        """
        return query.options(joinedload(URL.owner), selectinload(URL.tags))