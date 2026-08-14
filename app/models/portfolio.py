from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.influencer import InfluencerProfile


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    influencer_id: Mapped[int] = mapped_column(
        ForeignKey("influencer_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campaign_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    campaign_result: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Many-to-one relationship with InfluencerProfile
    influencer: Mapped["InfluencerProfile"] = relationship(back_populates="portfolios")
