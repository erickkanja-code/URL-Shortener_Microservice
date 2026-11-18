"""Database connection setup.

Creates the single SQLAlchemy engine (and its connection pool) for the app,
and provides `get_db`, the dependency that gives each request its own session.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def get_db() -> Iterator[Session]:
    """Yield a database session for one request, and close it afterwards.

    The session borrows a connection from the engine's pool when it first
    needs one, and returns it when the `with` block ends, even if the
    request raised an error.
    """
    with Session(engine) as session:
        yield session