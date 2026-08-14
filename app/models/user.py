import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import BrandProfile
    from app.models.influencer import InfluencerProfile
    from app.models.content import ContentComment, StatusLog
    from app.models.message import Message
    from app.models.notification import Notification



class UserRole(str, enum.Enum):
    brand = "brand"
    influencer = "influencer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.brand)
    profile_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to BrandProfile
    brand_profile: Mapped["BrandProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Relationship to InfluencerProfile
    influencer_profile: Mapped["InfluencerProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Relationship to ContentComment
    content_comments: Mapped[list["ContentComment"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    # Relationship to StatusLog
    status_logs: Mapped[list["StatusLog"]] = relationship(
        back_populates="actor", cascade="all, delete-orphan"
    )

    # Relationship to Messages
    sent_messages: Mapped[list["Message"]] = relationship(
        foreign_keys="[Message.sender_id]", back_populates="sender", cascade="all, delete-orphan"
    )
    received_messages: Mapped[list["Message"]] = relationship(
        foreign_keys="[Message.receiver_id]", back_populates="receiver", cascade="all, delete-orphan"
    )

    # Relationship to Notifications
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
