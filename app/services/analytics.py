"""Business logic for URL analytics."""

from sqlalchemy.orm import Session

from app.managers.click import ClickManager
from app.models import User
from app.schemas.analytics import AnalyticsResponse, CountryClicks, DailyClicks
from app.services.tiers import ensure_can_view_analytics
from app.services.url import ensure_owner, get_url


def get_url_analytics(db: Session, short_code: str, user: User) -> AnalyticsResponse:
    """Return clicks per day and per country for one of the user's URLs.

    Raises 404 if the short code does not exist, 403 if the user does not
    own the URL, and 403 if the user is not Premium. All counting is done
    in SQL by ClickManager.
    """
    url = get_url(db, short_code)
    ensure_owner(url, user)
    ensure_can_view_analytics(user)

    per_day = db.execute(ClickManager.clicks_per_day(url.id)).all()
    per_country = db.execute(ClickManager.clicks_per_country(url.id)).all()

    return AnalyticsResponse(
        short_code=url.short_code,
        total_clicks=url.click_count,
        clicks_per_day=[DailyClicks(day=row.day, total_clicks=row.total_clicks) for row in per_day],
        clicks_per_country=[
            CountryClicks(country=row.country, total_clicks=row.total_clicks) for row in per_country
        ],
    )