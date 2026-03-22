from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter(tags=["infra"])

@router.get(
    "/health",
    summary="Health check",
    description="Verifica se a API está no ar.",
    response_model=HealthResponse,
)
def health():
    return {"status": "ok"}
