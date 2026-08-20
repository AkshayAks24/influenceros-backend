from pydantic import BaseModel
from app.models.application import AssignmentPhase

class AssignmentPhaseUpdate(BaseModel):
    phase: AssignmentPhase

class LiveUrlCreate(BaseModel):
    live_url: str
