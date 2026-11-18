"""Shared fixtures for the test suite.

The tests run against a real PostgreSQL database, set by TEST_DATABASE_URL,
because the app relies on Postgres features such as INET columns,
timezone-aware timestamps and CAST to DATE. That database must be separate
from the development one: every table in it is emptied after each test.

Lifecycle:
- once per test run: drop and recreate all tables from the models
- before each test: seed the default tags
- after each test: empty every table, so tests never affect each other
"""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models import Base, Tag, Tier, User

load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]
DEFAULT_TAGS = ["Marketing", "Social", "Personal", "Work", "News"]

if TEST_DATABASE_URL == os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "TEST_DATABASE_URL must point to a separate database: the tests delete all data in it."
    )


@pytest.fixture(scope="session")
def engine():
    """Create the test engine and fresh tables, once for the whole test run."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    """Give a test a database session with the default tags already seeded.

    After the test, every table is emptied and the id counters are reset.
    """
    with Session(engine) as session:
        session.add_all([Tag(name=name) for name in DEFAULT_TAGS])
        session.commit()
        yield session

    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE users, urls, clicks, tags, url_tags RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def client(db_session):
    """Give a test an HTTP client for the app, wired to the test database.

    `dependency_overrides` makes every endpoint receive the test's session
    instead of a session on the development database.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user(db_session) -> User:
    """A free-tier user who owns URLs in the tests."""
    user = User(email="free@example.com")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def other_user(db_session) -> User:
    """A second user, for checking that users cannot see each other's URLs."""
    user = User(email="premium@example.com", is_premium=True, tier=Tier.PREMIUM)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def query_counter(engine):
    """Record every SQL statement sent to the database during a test.

    The test receives a list; each statement is appended as it runs, so
    `len(query_counter)` is the number of queries executed.
    """
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    yield statements
    event.remove(engine, "before_cursor_execute", record)