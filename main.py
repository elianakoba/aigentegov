from fastapi import FastAPI
from app.core.config import settings
from app.routers.health import router as health_router
from app.routers.sdpd import router as sdpd_router
from app.routers.historico import router as historico_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="APIs do AiGENTEGOV para SDPD (consulta e integrações com legado)."
)

app.include_router(health_router)
app.include_router(sdpd_router)
app.include_router(historico_router)
