"""Tests for the Premium-only analytics endpoint, GET /api/v1/analytics/{short_code}/.

In these tests, `user` is on the Free tier and `other_user` is Premium.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from app.models import URL, Click
from tests.helpers import analytics_path, create_url


def add_clicks(db_session, short_code, clicks):
    """Insert clicks for a URL directly, as (country, clicked_at) pairs."""
    url = db_session.scalars(select(URL).where(URL.short_code == short_code)).one()
    for country, clicked_at in clicks:
        db_session.add(
            Click(url_id=url.id, ip_address="1.2.3.4", user_agent="", country=country, clicked_at=clicked_at)
        )
    db_session.commit()


def test_analytics_returns_clicks_per_day_and_per_country(client, db_session, other_user_headers):
    created = create_url(client, other_user_headers)
    day_one = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    day_two = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
    add_clicks(
        db_session,
        created["short_code"],
        [("Rwanda", day_one), ("Rwanda", day_one), ("Ghana", day_two)],
    )

    response = client.get(analytics_path(created["short_code"]), headers=other_user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["short_code"] == created["short_code"]
    assert body["clicks_per_day"] == [
        {"day": "2026-11-01", "total_clicks": 2},
        {"day": "2026-11-02", "total_clicks": 1},
    ]
    assert body["clicks_per_country"] == [
        {"country": "Rwanda", "total_clicks": 2},
        {"country": "Ghana", "total_clicks": 1},
    ]


def test_analytics_total_clicks_counts_redirects(client, other_user_headers):
    created = create_url(client, other_user_headers)
    for _ in range(2):
        client.get(f"/{created['short_code']}/", follow_redirects=False)

    body = client.get(analytics_path(created["short_code"]), headers=other_user_headers).json()

    assert body["total_clicks"] == 2
    assert sum(day["total_clicks"] for day in body["clicks_per_day"]) == 2


def test_free_user_cannot_see_analytics_even_for_their_own_url(client, user_headers):
    created = create_url(client, user_headers)

    response = client.get(analytics_path(created["short_code"]), headers=user_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Detailed analytics are a Premium feature"


def test_premium_user_cannot_see_analytics_for_someone_elses_url(
    client, user_headers, other_user_headers
):
    created = create_url(client, user_headers)

    response = client.get(analytics_path(created["short_code"]), headers=other_user_headers)

    assert response.status_code == 403


def test_analytics_returns_404_for_unknown_code(client, other_user_headers):
    response = client.get(analytics_path("unknown"), headers=other_user_headers)

    assert response.status_code == 404


def test_analytics_requires_a_token(client):
    assert client.get(analytics_path("abc")).status_code == 401