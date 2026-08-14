from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import BrandProfile
    from app.models.influencer import InfluencerProfile


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brand_profiles.id", ondelete="CASCADE"), index=True
    )
    influencer_id: Mapped[int] = mapped_column(
        ForeignKey("influencer_profiles.id", ondelete="CASCADE"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("brand_id", "influencer_id", name="uix_brand_favorite_influencer"),
    )

    # Relationships
    brand: Mapped["BrandProfile"] = relationship(back_populates="favorites")
    influencer: Mapped["InfluencerProfile"] = relationship(back_populates="favorited_by")
