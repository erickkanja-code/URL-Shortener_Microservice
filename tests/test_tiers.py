"""Tests for the Free vs Premium tier rules.

In these tests, `user` is on the Free tier and `other_user` is Premium.
"""

from datetime import datetime, timedelta, timezone

from app.models import URL, Tier, User
from app.services.tiers import FREE_ACTIVE_URL_LIMIT, has_premium_access
from tests.helpers import URLS_ENDPOINT, create_url, url_detail


def create_many_urls(client, headers, count):
    """Create `count` URLs with different addresses and return their bodies."""
    return [create_url(client, headers, f"https://example.com/{number}") for number in range(count)]


# ---------- Who counts as Premium ----------

def test_premium_and_admin_tiers_have_premium_access():
    assert has_premium_access(User(tier=Tier.PREMIUM)) is True
    assert has_premium_access(User(tier=Tier.ADMIN)) is True
    assert has_premium_access(User(tier=Tier.FREE)) is False


# ---------- Active URL limit ----------

def test_free_user_cannot_go_over_the_active_url_limit(client, user_headers):
    create_many_urls(client, user_headers, FREE_ACTIVE_URL_LIMIT)

    response = client.post(
        URLS_ENDPOINT, json={"original_url": "https://one-too-many.com"}, headers=user_headers
    )

    assert response.status_code == 403
    body = client.get(URLS_ENDPOINT, params={"size": 100}, headers=user_headers).json()
    assert body["total"] == FREE_ACTIVE_URL_LIMIT


def test_premium_user_has_no_active_url_limit(client, other_user_headers):
    create_many_urls(client, other_user_headers, FREE_ACTIVE_URL_LIMIT + 1)

    body = client.get(URLS_ENDPOINT, params={"size": 100}, headers=other_user_headers).json()
    assert body["total"] == FREE_ACTIVE_URL_LIMIT + 1


def test_deactivated_urls_do_not_count_toward_the_limit(client, user_headers):
    urls = create_many_urls(client, user_headers, FREE_ACTIVE_URL_LIMIT)
    client.delete(url_detail(urls[0]["short_code"]), headers=user_headers)

    response = client.post(
        URLS_ENDPOINT, json={"original_url": "https://room-for-one.com"}, headers=user_headers
    )

    assert response.status_code == 201


def test_expired_urls_do_not_count_toward_the_limit(client, db_session, user, user_headers):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    for number in range(FREE_ACTIVE_URL_LIMIT):
        db_session.add(
            URL(
                original_url=f"https://old.com/{number}",
                short_code=f"old{number}",
                owner_id=user.id,
                expires_at=yesterday,
            )
        )
    db_session.commit()

    response = client.post(URLS_ENDPOINT, json={"original_url": "https://new.com"}, headers=user_headers)

    assert response.status_code == 201


def test_free_user_cannot_reactivate_a_url_over_the_limit(client, user_headers):
    urls = create_many_urls(client, user_headers, FREE_ACTIVE_URL_LIMIT)
    first = urls[0]["short_code"]
    client.delete(url_detail(first), headers=user_headers)
    create_url(client, user_headers, "https://takes-the-free-slot.com")

    response = client.put(url_detail(first), json={"is_active": True}, headers=user_headers)

    assert response.status_code == 403
    assert client.get(url_detail(first), headers=user_headers).json()["is_active"] is False


# ---------- Custom aliases ----------

def test_free_user_cannot_use_a_custom_alias(client, user_headers):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "custom_alias": "my-link"},
        headers=user_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Custom aliases are a Premium feature"


def test_premium_user_can_use_a_custom_alias(client, other_user_headers):
    body = create_url(client, other_user_headers, custom_alias="my-link")

    assert body["short_code"] == "my-link"