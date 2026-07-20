from typing import Literal

from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    technician_note: str = Field(
        ...,
        min_length=10,
        description="Rapport rédigé par le technicien.",
    )


class DiagnoseResponse(BaseModel):
    equipment_id: str
    symptom: str
    severity: Literal["low", "medium", "high", "critical"]
    failure_hypothesis: str
    recommended_action: str
    confidence: float = Field(
        ge=0,
        le=1,
    )
    evidence: list[str]
    requires_human_review: bool