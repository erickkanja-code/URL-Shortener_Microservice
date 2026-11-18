"""The User model and its subscription tiers."""

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.url import URL


class Tier(StrEnum):
    """Subscription tiers a user can belong to."""

    FREE = "Free"
    PREMIUM = "Premium"
    ADMIN = "Admin"


class User(Base):
    """A user who owns short URLs."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_premium: Mapped[bool] = mapped_column(default=False)
    tier: Mapped[Tier] = mapped_column(
        SQLAlchemyEnum(
            Tier,
            native_enum=False,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=Tier.FREE,
    )

    urls: Mapped[list["URL"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )