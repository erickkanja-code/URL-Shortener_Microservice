from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Tier(StrEnum):
    FREE = "Free"
    PREMIUM = "Premium"
    ADMIN = "Admin"


class Base(DeclarativeBase):
    pass


# Association table for the many-to-many relationship between URLs and tags.
url_tags = Table(
    "url_tags",
    Base.metadata,
    Column("url_id", ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
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


class URL(Base):
    __tablename__ = "urls"
    __table_args__ = (
        CheckConstraint("click_count >= 0", name="ck_urls_click_count_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str] = mapped_column(String(2048))
    short_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    custom_alias: Mapped[str | None] = mapped_column(String(50), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    favicon: Mapped[str | None] = mapped_column(String(2048))
    click_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    owner: Mapped["User"] = relationship(back_populates="urls")
    clicks: Mapped[list["Click"]] = relationship(
        back_populates="url", cascade="all, delete-orphan", passive_deletes=True
    )
    tags: Mapped[list["Tag"]] = relationship(secondary=url_tags, back_populates="urls")


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("urls.id", ondelete="CASCADE"))
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[str] = mapped_column(INET)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    user_agent: Mapped[str] = mapped_column(Text)
    referrer: Mapped[str | None] = mapped_column(String(2048))

    url: Mapped["URL"] = relationship(back_populates="clicks")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    urls: Mapped[list["URL"]] = relationship(secondary=url_tags, back_populates="tags")