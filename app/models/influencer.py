import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.application import CampaignApplication, CampaignAssignment
    from app.models.review import Review
    from app.models.favorite import Favorite


class VerificationStatus(str, enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"


class InfluencerProfile(Base):
    __tablename__ = "influencer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    platforms: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    audience_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    trust_score_breakdown: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    profile_completion: Mapped[int] = mapped_column(Integer, default=0)
    pricing: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.unverified
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # One-to-one relationship with User
    user: Mapped["User"] = relationship(back_populates="influencer_profile")

    # One-to-many relationship with Portfolio
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="influencer", cascade="all, delete-orphan"
    )

    applications: Mapped[list["CampaignApplication"]] = relationship(
        back_populates="influencer"
    )

    assignments: Mapped[list["CampaignAssignment"]] = relationship(
        back_populates="influencer"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="influencer"
    )

    favorited_by: Mapped[list["Favorite"]] = relationship(
        back_populates="influencer"
    )
