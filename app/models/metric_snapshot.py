import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OwnerType(str, enum.Enum):
    influencer = "influencer"
    brand = "brand"


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_type: Mapped[OwnerType] = mapped_column(Enum(OwnerType))
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    metric_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[date] = mapped_column(Date)
