from pydantic import BaseModel
from app.models.application import AssignmentPhase

class AssignmentPhaseUpdate(BaseModel):
    phase: AssignmentPhase
