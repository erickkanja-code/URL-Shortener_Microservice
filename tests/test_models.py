"""Tests for database-level rules: constraints and cascading deletes."""

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import URL, Click


def test_short_code_must_be_unique(db_session, user):
    db_session.add(URL(original_url="https://a.com", short_code="same", owner_id=user.id))
    db_session.commit()

    db_session.add(URL(original_url="https://b.com", short_code="same", owner_id=user.id))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_click_count_cannot_be_negative(db_session, user):
    db_session.add(
        URL(original_url="https://a.com", short_code="neg", owner_id=user.id, click_count=-1)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_deleting_a_user_deletes_their_urls_and_clicks(db_session, user):
    url = URL(original_url="https://a.com", short_code="abc", owner_id=user.id)
    db_session.add(url)
    db_session.commit()
    db_session.add(Click(url_id=url.id, ip_address="1.2.3.4", user_agent="test"))
    db_session.commit()

    db_session.delete(user)
    db_session.commit()

    assert db_session.scalars(select(URL)).all() == []
    assert db_session.scalars(select(Click)).all() == []


def test_foreign_keys_used_in_lookups_are_indexed(engine):
    inspector = inspect(engine)
    url_indexes = {tuple(index["column_names"]) for index in inspector.get_indexes("urls")}
    click_indexes = {tuple(index["column_names"]) for index in inspector.get_indexes("clicks")}

    assert ("owner_id",) in url_indexes
    assert ("url_id",) in click_indexes