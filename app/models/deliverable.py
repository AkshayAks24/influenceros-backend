from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(255))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Many-to-one relationship with Campaign
    campaign: Mapped["Campaign"] = relationship(back_populates="deliverables")
