from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import Enum as SQLAlchemyEnum, DateTime, Boolean, String
from enum import Enum
from datetime import datetime
class Tier(Enum):
    FREE = "Free"
    PREMIUM="Premium"
    ADMIN="Admin"
    
    
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    tier: Mapped[Tier] = mapped_column(SQLAlchemyEnum(Tier), default=Tier.FREE)
    
    
class URL(Base):
    __tablename__ = "urls"
    
    original_url: Mapped[str]
    short_code: Mapped[str]
    custom_alias: Mapped[str]
    owner: Mapped[int]
    is_active: Mapped[bool]
    expires_at: Mapped[datetime | None]
    title: Mapped[str | None]
    description: Mapped[str | None]
    title: Mapped[str | None]
    favicon_url: Mapped[str | None]
    

