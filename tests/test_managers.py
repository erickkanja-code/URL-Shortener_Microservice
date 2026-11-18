"""Tests for the reusable queries in URLManager and ClickManager."""

from datetime import datetime, timedelta, timezone

from app.managers.click import ClickManager
from app.managers.url import URLManager
from app.models import URL, Click, Tag

NOW = datetime.now(timezone.utc)


def add_url(db_session, owner, short_code, **fields) -> URL:
    """Insert a URL directly into the database and return it."""
    url = URL(
        original_url=f"https://example.com/{short_code}",
        short_code=short_code,
        owner_id=owner.id,
        **fields,
    )
    db_session.add(url)
    db_session.commit()
    return url


def short_codes(db_session, query) -> list[str]:
    """Run a query and return the short codes of the URLs it found."""
    return [url.short_code for url in db_session.scalars(query).all()]


def test_active_urls_excludes_inactive_and_expired(db_session, user):
    add_url(db_session, user, "no-expiry")
    add_url(db_session, user, "future", expires_at=NOW + timedelta(days=1))
    add_url(db_session, user, "expired", expires_at=NOW - timedelta(days=1))
    add_url(db_session, user, "inactive", is_active=False)

    result = short_codes(db_session, URLManager.active_urls())

    assert sorted(result) == ["future", "no-expiry"]


def test_expired_urls_only_returns_urls_past_their_expiry(db_session, user):
    add_url(db_session, user, "no-expiry")
    add_url(db_session, user, "future", expires_at=NOW + timedelta(days=1))
    add_url(db_session, user, "expired", expires_at=NOW - timedelta(days=1))

    result = short_codes(db_session, URLManager.expired_urls())

    assert result == ["expired"]


def test_popular_urls_are_ordered_by_click_count(db_session, user):
    add_url(db_session, user, "low", click_count=1)
    add_url(db_session, user, "high", click_count=50)
    add_url(db_session, user, "middle", click_count=10)

    result = short_codes(db_session, URLManager.popular_urls())

    assert result == ["high", "middle", "low"]


def test_with_owner_and_tags_avoids_n_plus_one_queries(db_session, user, other_user, query_counter):
    tags = db_session.query(Tag).all()
    for number in range(10):
        owner = user if number % 2 == 0 else other_user
        add_url(db_session, owner, f"code{number}", tags=tags[:2])
    db_session.expunge_all()  # forget loaded objects, so nothing is already in memory
    query_counter.clear()

    urls = db_session.scalars(URLManager.with_owner_and_tags(URLManager.active_urls())).all()
    for url in urls:
        _ = url.owner.email, [tag.name for tag in url.tags]

    assert len(urls) == 10
    assert len(query_counter) == 2  # one for URLs with owners, one for all tags


def test_clicks_per_country_counts_and_orders_by_total(db_session, user):
    url = add_url(db_session, user, "abc")
    for country in ["Rwanda", "Ghana", "Rwanda", "Rwanda", "Ghana", None]:
        db_session.add(Click(url_id=url.id, ip_address="1.2.3.4", user_agent="", country=country))
    db_session.commit()

    rows = db_session.execute(ClickManager.clicks_per_country(url.id)).all()

    assert [(row.country, row.total_clicks) for row in rows] == [
        ("Rwanda", 3),
        ("Ghana", 2),
        (None, 1),
    ]


def test_clicks_per_day_groups_clicks_by_date(db_session, user):
    url = add_url(db_session, user, "abc")
    day_one = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    day_two = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
    for clicked_at in [day_one, day_one, day_two]:
        db_session.add(
            Click(url_id=url.id, ip_address="1.2.3.4", user_agent="", clicked_at=clicked_at)
        )
    db_session.commit()

    rows = db_session.execute(ClickManager.clicks_per_day(url.id)).all()

    assert [(str(row.day), row.total_clicks) for row in rows] == [
        ("2026-11-01", 2),
        ("2026-11-02", 1),
    ]


def test_click_analytics_only_count_the_requested_url(db_session, user):
    first = add_url(db_session, user, "first")
    second = add_url(db_session, user, "second")
    db_session.add(Click(url_id=first.id, ip_address="1.2.3.4", user_agent="", country="Kenya"))
    db_session.add(Click(url_id=second.id, ip_address="1.2.3.4", user_agent="", country="Kenya"))
    db_session.commit()

    rows = db_session.execute(ClickManager.clicks_per_country(first.id)).all()

    assert [(row.country, row.total_clicks) for row in rows] == [("Kenya", 1)]