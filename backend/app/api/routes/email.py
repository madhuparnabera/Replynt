from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_model_service
from app.core.config import get_settings
from app.models.schemas import AnalyzeEmailResponse, EmailRequest, HealthResponse
from app.services.commitment_service import commitment_service
from app.models.schemas_commitment import ExtractCommitmentsRequest
from app.services.model_service import ModelService

router = APIRouter(tags=["email-analysis"])

COMMITMENT_INTENTS = {
    "request",
    "follow_up",
    "action_required",
    "question",
    "complaint",
    "escalation",
}


@router.get("/health", response_model=HealthResponse)
def health_check(
    model_service: ModelService = Depends(get_model_service),
) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        models_loaded=model_service.is_ready,
        loaded_models=model_service.loaded_model_names(),
    )


@router.post("/analyze-email", response_model=AnalyzeEmailResponse)
def analyze_email(
    payload: EmailRequest,
    model_service: ModelService = Depends(get_model_service),
) -> AnalyzeEmailResponse:
    try:
        result = model_service.analyze_email(payload.subject, payload.body)

        # Determine if this email may contain a commitment
        may_contain_commitment = (
            not result.get("junk", False)
            and str(result.get("intent", "")).lower().replace(" ", "_") in COMMITMENT_INTENTS
        )
        result["may_contain_commitment"] = may_contain_commitment

        # If commitment is likely, run extraction inline and embed in response
        commitments = []
        if may_contain_commitment:
            extraction = commitment_service.extract_and_optionally_save(
                ExtractCommitmentsRequest(
                    subject=payload.subject,
                    body=payload.body,
                    auto_save=True,
                )
            )
            commitments = [c.model_dump() for c in extraction.commitments]

        result["commitments"] = commitments
        result["commitments_count"] = len(commitments)

        return AnalyzeEmailResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email analysis failed") from exc