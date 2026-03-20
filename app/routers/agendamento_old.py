from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.security import validar_api_key
from app.schemas.agendamento import (
    AgendamentoVariavelCreateRequest,
    AgendamentoResponse
)
from app.services.agendamento_variavel import criar_agendamento_variavel
from app.db.agendamento import (
    buscar_agendamento_por_id,
    buscar_agendamento_por_prontuario,
    atualizar_status_agendamento
)

router = APIRouter(
    prefix="/v1/agendamentos",
    tags=["Agendamentos"],
)


# =========================================================
# POST - Agendamento Variável
# =========================================================
@router.post(
    "/variavel",
    summary="Registrar solicitação de agendamento com evento de tempo variável",
    description=(
        "Registra uma solicitação de agendamento para serviços do tipo evento variável.\n\n"
        "Neste modelo não há consulta prévia de disponibilidade ou bloqueio de horário.\n"
        "A requisição apenas registra a intenção do cidadão.\n\n"
        "Regras do processo:\n"
        "- O status inicial será sempre 'SOLICITADO'.\n"
        "- Não há validação de grade horária neste endpoint.\n"
        "- A confirmação do atendimento será realizada posteriormente pela equipe responsável.\n\n"
        "Padrões de integração:\n"
        "- servicoespecializado: exemplo 'TRANSPORTE'.\n"
        "- canal padrão: 'WHATSAPP'.\n"
        "- solicitado_por padrão: 'AGENTE_IA'.\n"
    ),
    status_code=status.HTTP_201_CREATED,
    response_model=AgendamentoResponse,  # <-- CORRIGIDO (não é lista)
    dependencies=[Depends(validar_api_key)],
)
def post_agendamento_variavel(payload: AgendamentoVariavelCreateRequest):
    row = criar_agendamento_variavel(payload.model_dump())
    return dict(row)  # <-- conversão segura


# =========================================================
# GET - Buscar por prontuário (retorna 0..N registros)
# =========================================================
@router.get( "/prontuario/{prontuariogapd}",
    summary="Consultar se cidadão tem serviço agendamento por prontuário",
    response_model=List[AgendamentoResponse],
    status_code=status.HTTP_200_OK,responses={
        404: {"description": "Nenhum agendamento encontrado"},
        500: {"description": "Erro interno no servidor"}
    },

    dependencies=[Depends(validar_api_key)],
)
def get_agendamentos_por_prontuario(prontuariogapd: int):
    """
    Retorna os agendamentos futuros do cidadão, caso existam,
    a partir do número de prontuário.
    """
    try:
        rows = buscar_agendamento_por_prontuario(prontuariogapd)
        return [dict(r) for r in rows]  # <-- conversão segura
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar agendamento: {str(e)}"
        )


# =========================================================
# GET - Buscar por ID
# =========================================================
@router.get(
    "/{id_agendamento}",
    summary="Consultar agendamento por ID",
    status_code=status.HTTP_200_OK,
    response_model=AgendamentoResponse,
    dependencies=[Depends(validar_api_key)],
)
def get_agendamento(id_agendamento: int):
    row = buscar_agendamento_por_id(id_agendamento)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )

    return dict(row)  # <-- conversão segura


# =========================================================
# PATCH - Atualizar Status
# =========================================================
@router.patch(
    "/{id_agendamento}/status",
    summary="Atualizar status do agendamento",
    status_code=status.HTTP_200_OK,
    response_model=AgendamentoResponse,
    dependencies=[Depends(validar_api_key)],
)
def patch_status(id_agendamento: int, status_novo: str, motivo: str | None = None):
    row = atualizar_status_agendamento(id_agendamento, status_novo, motivo)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado"
        )

    return dict(row)  # <-- conversão segura