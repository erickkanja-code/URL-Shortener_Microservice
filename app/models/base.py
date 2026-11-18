"""The declarative base class that every model inherits from."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models.

    Every model that inherits from it registers its table on
    `Base.metadata`, which Alembic reads to generate migrations.
    """