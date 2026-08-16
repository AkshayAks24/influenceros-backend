from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import BrandProfile
    from app.models.campaign import Campaign
    from app.models.influencer import InfluencerProfile


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    influencer_id: Mapped[int] = mapped_column(
        ForeignKey("influencer_profiles.id", ondelete="CASCADE"), index=True
    )
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brand_profiles.id", ondelete="CASCADE"), index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)  # Expected 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    influencer: Mapped["InfluencerProfile"] = relationship(back_populates="reviews")
    brand: Mapped["BrandProfile"] = relationship(back_populates="reviews")
    campaign: Mapped["Campaign | None"] = relationship(back_populates="reviews")

    __table_args__ = (
        UniqueConstraint(
            "brand_id", "influencer_id", "campaign_id", name="uix_review_brand_influencer_campaign"
        ),
    )
