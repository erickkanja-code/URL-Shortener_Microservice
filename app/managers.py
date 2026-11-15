from sqlalchemy import Date, Select, cast, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from .models import URL, Click


class URLManager:
    @staticmethod
    def active_urls() -> Select:
        return select(URL).where(
            URL.is_active.is_(True),
            or_(URL.expires_at.is_(None), URL.expires_at > func.now()),
        )

    @staticmethod
    def expired_urls() -> Select:
        return select(URL).where(URL.expires_at <= func.now())

    @staticmethod
    def popular_urls() -> Select:
        return select(URL).order_by(URL.click_count.desc())

    @staticmethod
    def with_owner_and_tags(query: Select) -> Select:
        # Prevents the N+1 problem when the caller will use url.owner or url.tags.
        # joinedload  -> owner is fetched in the same query with a JOIN (like select_related).
        # selectinload -> tags are fetched in one extra query using IN (like prefetch_related).
        return query.options(joinedload(URL.owner), selectinload(URL.tags))


class ClickManager:
    @staticmethod
    def clicks_per_country(url_id: int) -> Select:
        total_clicks = func.count(Click.id).label("total_clicks")
        return (
            select(Click.country, total_clicks)
            .where(Click.url_id == url_id)
            .group_by(Click.country)
            .order_by(total_clicks.desc())
        )

    @staticmethod
    def clicks_per_day(url_id: int) -> Select:
        day = cast(Click.clicked_at, Date).label("day")
        total_clicks = func.count(Click.id).label("total_clicks")
        return (
            select(day, total_clicks)
            .where(Click.url_id == url_id)
            .group_by(day)
            .order_by(day)
        )