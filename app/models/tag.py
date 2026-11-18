"""The Tag model, used to categorize URLs."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.url import url_tags

if TYPE_CHECKING:
    from app.models.url import URL


class Tag(Base):
    """A label such as "Marketing" that can be attached to many URLs."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    urls: Mapped[list["URL"]] = relationship(secondary=url_tags, back_populates="tags")