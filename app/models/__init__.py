"""Database models.

Every model is imported here so that importing `app.models` registers all
tables on `Base.metadata`. Alembic relies on this to see every table, and
SQLAlchemy relies on it to resolve relationships between models by name.
"""

from app.models.base import Base
from app.models.click import Click
from app.models.tag import Tag
from app.models.url import URL, url_tags
from app.models.user import Tier, User

__all__ = ["Base", "Click", "Tag", "Tier", "URL", "User", "url_tags"]