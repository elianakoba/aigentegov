from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from app.core.security import validar_api_key
from app.schemas.notificacao import NotificacaoResponse
from app.db.notificacao import listar_notificacoes, buscar_notificacao_por_id


router = APIRouter(
    prefix="/v1/notificacoes",
    tags=["Notificações"],
    dependencies=[Depends(validar_api_key)]
)


@router.get(
    "",
    response_model=List[NotificacaoResponse],
    summary="Listar notificações"
)
def listar_notificacao():
    """
    Retorna todas as notificações cadastradas.
    """
    try:
        return listar_notificacoes()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar notificações: {str(e)}"
        )


@router.get(
    "/{id_notificacao}",
    response_model=NotificacaoResponse,
    summary="Consultar notificação por ID"
)
def consultar_notificacao_por_id(id_notificacao: int):
    """
    Retorna uma notificação específica para confirmação de horário.
    """
    try:
        notificacao = buscar_notificacao_por_id(id_notificacao)

        if not notificacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificação não encontrada"
            )

        return notificacao

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar notificação: {str(e)}"
        )