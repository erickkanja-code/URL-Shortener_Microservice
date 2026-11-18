"""Tests for the public redirect endpoint, GET /{short_code}/."""

from sqlalchemy import select

from app.models import Click
from tests.helpers import URLS_ENDPOINT, create_url


def visit(client, short_code, **headers):
    """Visit a short link without following the redirect, so the 302 can be checked."""
    return client.get(f"/{short_code}/", headers=headers, follow_redirects=False)


def test_redirect_sends_302_to_the_original_url(client, user):
    created = create_url(client, user.id, "https://example.com/page")

    response = visit(client, created["short_code"])

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/page"


def test_redirect_records_a_click(client, db_session, user):
    created = create_url(client, user.id)

    visit(client, created["short_code"], referer="https://google.com", **{"user-agent": "TestBrowser"})

    click = db_session.scalars(select(Click)).one()
    assert click.referrer == "https://google.com"
    assert click.user_agent == "TestBrowser"
    assert str(click.ip_address) == "0.0.0.0"  # the test client has no real IP address


def test_each_visit_increments_click_count(client, user):
    created = create_url(client, user.id)

    for _ in range(3):
        visit(client, created["short_code"])

    body = client.get(
        f"{URLS_ENDPOINT}{created['short_code']}/", params={"owner_id": user.id}
    ).json()
    assert body["click_count"] == 3


def test_redirect_returns_404_for_unknown_code(client):
    assert visit(client, "unknown").status_code == 404


def test_redirect_returns_404_for_deactivated_url(client, user):
    created = create_url(client, user.id)
    client.delete(f"{URLS_ENDPOINT}{created['short_code']}/", params={"owner_id": user.id})

    assert visit(client, created["short_code"]).status_code == 404


def test_redirect_returns_404_for_expired_url(client, db_session, user):
    created = create_url(client, user.id, expires_at="2020-01-01T00:00:00Z")

    assert visit(client, created["short_code"]).status_code == 404
    assert db_session.scalars(select(Click)).all() == []