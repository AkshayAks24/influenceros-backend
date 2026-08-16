from pydantic import BaseModel, ConfigDict
from app.models.pricing_plan import BillingCycle

class PricingPlanResponse(BaseModel):
    id: int
    name: str
    price: float
    billing_cycle: BillingCycle
    features: list[str]
    is_highlighted: bool
    
    model_config = ConfigDict(from_attributes=True)
