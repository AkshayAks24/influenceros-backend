import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.influencer import InfluencerProfile
    from app.models.content import SubmittedContent


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class CampaignApplication(Base):
    __tablename__ = "campaign_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    influencer_id: Mapped[int] = mapped_column(
        ForeignKey("influencer_profiles.id", ondelete="CASCADE"), index=True
    )
    proposal: Mapped[str] = mapped_column(Text)
    proposed_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.pending
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(back_populates="applications")
    influencer: Mapped["InfluencerProfile"] = relationship(back_populates="applications")
    assignment: Mapped["CampaignAssignment | None"] = relationship(
        back_populates="application", uselist=False
    )


class AssignmentPhase(str, enum.Enum):
    brief_sent = "brief_sent"
    content_creation = "content_creation"
    review = "review"
    approved = "approved"
    live = "live"
    completed = "completed"


class CampaignAssignment(Base):
    __tablename__ = "campaign_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    influencer_id: Mapped[int] = mapped_column(
        ForeignKey("influencer_profiles.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        unique=True,
    )

    current_phase: Mapped[AssignmentPhase] = mapped_column(
        Enum(AssignmentPhase), default=AssignmentPhase.brief_sent
    )

    live_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "influencer_id", name="uix_campaign_influencer_assignment"
        ),
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(back_populates="assignments")
    influencer: Mapped["InfluencerProfile"] = relationship(back_populates="assignments")
    application: Mapped["CampaignApplication | None"] = relationship(
        back_populates="assignment"
    )
    submitted_contents: Mapped[list["SubmittedContent"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )
