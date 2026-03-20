from fastapi import FastAPI

from app.core.config import settings

# Routers técnicos
from app.routers.health import router as health_router

# APIs AWS (Consulta Notificações)
from app.routers.notificacao import router as notificacao_router

# APIs AWS (Grava Status Notificações)
from app.routers.notificacao_status import router as notificacao_status_router


# Consultar paciente e prontuário do paciente
#from app.routers.cidadao import router as cidadao_router

# Localização do cidadão para agendamento
from app.routers.consultar_cidadao_atendimento import router as consultar_cidadao_atendimento_router

# ✅ Agendamentos
# from app.routers.disponibilidade import router as disponibilidade_router
from app.routers.agendamento import router as agendamento_router



# Validação de ambiente (evita subir "sem config" na AWS/Prod)
settings.validate_required()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="APIs do AiGENTEGOV para SDPD, Agendamento e integrações com sistemas legados",
    # Se quiser ocultar docs em produção, você pode ajustar assim:
    # docs_url=None if settings.ENV.lower() in {"prod", "production"} else "/docs",
    # redoc_url=None if settings.ENV.lower() in {"prod", "production"} else "/redoc",
)

# ---------------------------------------------------
# Rotas técnicas / saúde
# ---------------------------------------------------
app.include_router(health_router)

# ---------------------------------------------------
# Rotas AWS (Consulta de Notificações / Agente IA)
# ---------------------------------------------------
app.include_router(notificacao_router)

# ---------------------------------------------------
# Rotas AWS (Grava Status Notificações / Agente IA)
# ---------------------------------------------------
app.include_router(notificacao_status_router)

# -------------------------------------------------------
# Rotas para Consulta paciente e prontuário do paciente
# -------------------------------------------------------
#app.include_router(cidadao_router)

# ---------------------------------------------------
# ✅ Rotas de Disponibilidade (Agendamento)
# ---------------------------------------------------
# app.include_router(disponibilidade_router)


# ---------------------------------------------------
# ✅ Rotas para Localização do cidadão para agendamento (etapa prévia ao agendamento)
# trazer dados do cidadão e validar se pode prosseguir para o agendamento
# ---------------------------------------------------
app.include_router(consultar_cidadao_atendimento_router)


# ---------------------------------------------------
# ✅ Rotas de Agendamentos (criação/cancelamento etc. - conforme formos evoluindo)
# ---------------------------------------------------
app.include_router(agendamento_router)


