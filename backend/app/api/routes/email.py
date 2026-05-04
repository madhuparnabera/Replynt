from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_model_service
from app.core.config import get_settings
from app.models.schemas import AnalyzeEmailResponse, EmailRequest, HealthResponse
from app.services.model_service import ModelService

router = APIRouter(tags=["email-analysis"])


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
        return AnalyzeEmailResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email analysis failed") from exc
