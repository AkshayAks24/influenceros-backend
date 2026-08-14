import enum

from sqlalchemy import Boolean, Enum, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BillingCycle(str, enum.Enum):
    monthly = "monthly"
    annual = "annual"


class PricingPlan(Base):
    __tablename__ = "pricing_plans"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle))
    features: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False)
