"""Tests that short codes are always unique.

Random codes almost never collide, so these tests force collisions by
replacing `random_short_code` with a fake that returns chosen codes.
"""

from sqlalchemy import func, select

from app.models import URL
from app.services import url as url_service
from app.services.url import MAX_SHORT_CODE_ATTEMPTS, generate_short_code
from tests.helpers import URLS_ENDPOINT, create_url


def add_url_with_code(db_session, owner, short_code):
    """Insert a URL that already uses `short_code`."""
    db_session.add(URL(original_url="https://taken.com", short_code=short_code, owner_id=owner.id))
    db_session.commit()


def test_generator_skips_a_code_that_is_taken(db_session, user, monkeypatch):
    add_url_with_code(db_session, user, "TAKEN01")
    codes = iter(["TAKEN01", "FRESH01"])
    monkeypatch.setattr(url_service, "random_short_code", lambda: next(codes))

    assert generate_short_code(db_session) == "FRESH01"


def test_create_url_uses_a_fresh_code_after_a_collision(client, db_session, user, user_headers, monkeypatch):
    add_url_with_code(db_session, user, "TAKEN01")
    codes = iter(["TAKEN01", "FRESH01"])
    monkeypatch.setattr(url_service, "random_short_code", lambda: next(codes))

    body = create_url(client, user_headers, "https://example.com/new")

    assert body["short_code"] == "FRESH01"


def test_create_url_gives_up_after_too_many_collisions(client, db_session, user, user_headers, monkeypatch):
    add_url_with_code(db_session, user, "TAKEN01")
    attempts = []

    def always_taken():
        attempts.append(1)
        return "TAKEN01"

    monkeypatch.setattr(url_service, "random_short_code", always_taken)

    response = client.post(URLS_ENDPOINT, json={"original_url": "https://example.com/new"}, headers=user_headers)

    assert response.status_code == 503
    assert len(attempts) == MAX_SHORT_CODE_ATTEMPTS


def test_a_code_taken_between_check_and_insert_gives_409_not_500(
    client, db_session, user, user_headers, monkeypatch
):
    """Simulates the race: another request saves the same code after our check passed."""
    add_url_with_code(db_session, user, "RACED01")
    monkeypatch.setattr(url_service, "generate_short_code", lambda db: "RACED01")

    response = client.post(URLS_ENDPOINT, json={"original_url": "https://example.com/new"}, headers=user_headers)

    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(URL)) == 1


def test_an_alias_cannot_reuse_a_random_code(client, db_session, user, other_user_headers):
    add_url_with_code(db_session, user, "abc1234")

    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "custom_alias": "abc1234"},
        headers=other_user_headers,
    )

    assert response.status_code == 409