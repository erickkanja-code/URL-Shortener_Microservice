from sqlalchemy import Select, func, or_, select

from .models import URL


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