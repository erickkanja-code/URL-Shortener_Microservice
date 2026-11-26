"""Tests for the public redirect endpoint, GET /{short_code}/."""

from sqlalchemy import select

from app.core.geolocation import Location
from app.models import Click
from app.services import url as url_service
from tests.helpers import create_url, url_detail


def visit(client, short_code, **headers):
    """Visit a short link without following the redirect, so the 302 can be checked.

    No access token is sent: the redirect is public.
    """
    return client.get(f"/{short_code}/", headers=headers, follow_redirects=False)


def test_redirect_sends_302_to_the_original_url(client, user_headers):
    created = create_url(client, user_headers, "https://example.com/page")

    response = visit(client, created["short_code"])

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/page"


def test_redirect_records_a_click(client, db_session, user_headers):
    created = create_url(client, user_headers)

    visit(client, created["short_code"], referer="https://google.com", **{"user-agent": "TestBrowser"})

    click = db_session.scalars(select(Click)).one()
    assert click.referrer == "https://google.com"
    assert click.user_agent == "TestBrowser"
    assert str(click.ip_address) == "0.0.0.0"  # the test client has no real IP address


def test_redirect_records_the_visitors_location(client, db_session, user_headers, monkeypatch):
    monkeypatch.setattr(
        url_service, "lookup_location", lambda ip: Location(city="Kigali", country="Rwanda")
    )
    created = create_url(client, user_headers)

    visit(client, created["short_code"])

    click = db_session.scalars(select(Click)).one()
    assert click.city == "Kigali"
    assert click.country == "Rwanda"


def test_redirect_still_works_when_the_location_is_unknown(client, db_session, user_headers):
    created = create_url(client, user_headers, "https://example.com/page")

    response = visit(client, created["short_code"])  # the test client's IP has no location

    assert response.status_code == 302
    click = db_session.scalars(select(Click)).one()
    assert click.city is None
    assert click.country is None


def test_each_visit_increments_click_count(client, user_headers):
    created = create_url(client, user_headers)

    for _ in range(3):
        visit(client, created["short_code"])

    body = client.get(url_detail(created["short_code"]), headers=user_headers).json()
    assert body["click_count"] == 3


def test_redirect_returns_404_for_unknown_code(client):
    assert visit(client, "unknown").status_code == 404


def test_redirect_returns_404_for_deactivated_url(client, user_headers):
    created = create_url(client, user_headers)
    client.delete(url_detail(created["short_code"]), headers=user_headers)

    assert visit(client, created["short_code"]).status_code == 404


def test_redirect_returns_404_for_expired_url(client, db_session, user_headers):
    created = create_url(client, user_headers, expires_at="2020-01-01T00:00:00Z")

    assert visit(client, created["short_code"]).status_code == 404
    assert db_session.scalars(select(Click)).all() == []