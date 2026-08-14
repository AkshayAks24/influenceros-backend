import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import BrandProfile
    from app.models.deliverable import Deliverable
    from app.models.application import CampaignApplication, CampaignAssignment
    from app.models.content import StatusLog
    from app.models.review import Review


# draft/open/completed map directly to frontend; in_review and in_progress both display as frontend's 'In Review' vs progress badges — resolve display mapping in the frontend integration phase.
class CampaignStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    in_review = "in_review"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brand_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    budget: Mapped[float] = mapped_column(Float)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.draft
    )
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Many-to-one relationship with BrandProfile
    brand: Mapped["BrandProfile"] = relationship(back_populates="campaigns")

    # One-to-many relationship with Deliverable
    deliverables: Mapped[list["Deliverable"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    applications: Mapped[list["CampaignApplication"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    assignments: Mapped[list["CampaignAssignment"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    status_logs: Mapped[list["StatusLog"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="campaign"
    )
