from fastapi import FastAPI, HTTPException

from app.model_client import ModelClient
from app.schemas import DiagnoseRequest, DiagnoseResponse


app = FastAPI(
    title="DiagOps API",
    description="API d'assistance au diagnostic industriel.",
    version="0.1.0",
)

model_client = ModelClient()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "DiagOps API is running"}


@app.post(
    "/diagnose",
    response_model=DiagnoseResponse,
)
def diagnose(request: DiagnoseRequest) -> DiagnoseResponse:
    try:
        model_result = model_client.diagnose(
            request.technician_note
        )
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return DiagnoseResponse(
        equipment_id="unknown",
        symptom=model_result["symptom"],
        severity=model_result["severity"],
        failure_hypothesis=model_result["failure_hypothesis"],
        recommended_action=model_result["recommended_action"],
        confidence=model_result["confidence"],
        evidence=[request.technician_note],
        requires_human_review=model_result[
            "requires_human_review"
        ],
    )