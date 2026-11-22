"""Analytics endpoints, under /api/v1/analytics. Premium only."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, SessionDep
from app.schemas.analytics import AnalyticsResponse
from app.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{short_code}/", response_model=AnalyticsResponse)
def get_analytics(short_code: str, db: SessionDep, current_user: CurrentUserDep):
    """Return a URL's clicks per day and per country. Owner and Premium only."""
    return analytics_service.get_url_analytics(db, short_code, current_user)