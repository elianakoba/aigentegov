from fastapi import APIRouter, HTTPException, status, Depends

from app.core.security import validar_api_key
from app.schemas.notificacao_status import NotificacaoStatusUpdate
from app.db.notificacao_status import atualizar_status_notificacao


router = APIRouter(
    prefix="/v1/notificacoes",
    tags=["Notificações - Status"],
    dependencies=[Depends(validar_api_key)]
)


@router.post(
    "/{id_notificacao}/status",
    summary="Registrar atualização de status da notificação",
    status_code=status.HTTP_200_OK,
)
def gravar_status_notificacao(
    id_notificacao: int,
    payload: NotificacaoStatusUpdate,
):
    if not any([
        payload.situacaonotificacao,
        payload.observacaonotificacao,
        payload.situacaoresposta,
        payload.observacaoresposta,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie ao menos um campo para atualização."
        )

    result = atualizar_status_notificacao(
        id_notificacao=id_notificacao,
        situacaonotificacao=payload.situacaonotificacao,
        observacaonotificacao=payload.observacaonotificacao,
        situacaoresposta=payload.situacaoresposta,
        observacaoresposta=payload.observacaoresposta,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada."
        )

    return {
        "message": "Status da notificação atualizado com sucesso.",
        "data": result
    }
