from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import Campaign
    from app.models.review import Review
    from app.models.favorite import Favorite


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255))
    logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # One-to-one relationship with User
    user: Mapped["User"] = relationship(back_populates="brand_profile")

    # One-to-many relationship with Campaign
    campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )
