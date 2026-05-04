from app.core.config import get_settings
from app.services.model_service import ModelService

settings = get_settings()
model_service = ModelService(settings.models_dir)


def get_model_service() -> ModelService:
    return model_service
