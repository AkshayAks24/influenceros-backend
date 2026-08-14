import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import CampaignAssignment
    from app.models.campaign import Campaign
    from app.models.user import User


class ContentStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    changes_requested = "changes_requested"


class SubmittedContent(Base):
    __tablename__ = "submitted_content"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_assignments.id", ondelete="CASCADE"), index=True
    )
    media_url: Mapped[str] = mapped_column(String(1024))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.pending_review
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    assignment: Mapped["CampaignAssignment"] = relationship(
        back_populates="submitted_contents"
    )
    comments: Mapped[list["ContentComment"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )


class ContentComment(Base):
    __tablename__ = "content_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("submitted_content.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    comment: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    content: Mapped["SubmittedContent"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="content_comments")


class StatusLog(Base):
    __tablename__ = "status_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_status: Mapped[str] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(back_populates="status_logs")
    actor: Mapped["User | None"] = relationship(back_populates="status_logs")
