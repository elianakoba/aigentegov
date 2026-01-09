from fastapi import APIRouter, HTTPException, Depends
from app.core.security import require_api_key
from app.schemas.historico import CriarHistoricoRequest, CriarHistoricoResponse
from app.db.sqlserver import inserir_historico_sdpd, listar_historicos_por_pessoa

router = APIRouter(
    prefix="/v1/sdpd",
    tags=["SDPD - Histórico"],
    dependencies=[Depends(require_api_key)]
)

@router.post(
    "/historicos",
    response_model=CriarHistoricoResponse,
    summary="Registrar histórico SDPD",
    description="Grava um registro de histórico no legado (HistoricoSDPD)."
)
def criar_historico(payload: CriarHistoricoRequest):
    try:
        id_hist, data_gravacao = inserir_historico_sdpd(
            id_pessoa=payload.id_pessoa,
            historico=payload.historico,
            tipo_historico=payload.tipo_historico,
            id_usuario=payload.id_usuario
        )

        return {
            "id_historico": id_hist,
            "id_pessoa": payload.id_pessoa,
            "id_usuario": payload.id_usuario,
            "tipo_historico": payload.tipo_historico,
            "historico": payload.historico,
            "data": str(data_gravacao),
        }

    except Exception as e:
        print("Erro ao inserir histórico:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao gravar histórico")


@router.get(
    "/pessoas/{id_pessoa}/historicos",
    summary="Listar histórico por pessoa",
    description="Retorna os últimos registros de histórico da pessoa."
)
def listar_historico(id_pessoa: int, limit: int = 50):
    try:
        rows = listar_historicos_por_pessoa(id_pessoa=id_pessoa, limit=limit)
        # Retorno simples (pode evoluir para response_model depois)
        return [
            {
                "id_historico": int(r[0]),
                "id_pessoa": int(r[1]),
                "id_usuario": int(r[2]) if r[2] is not None else None,
                "tipo_historico": int(r[3]) if r[3] is not None else None,
                "historico": str(r[4]) if r[4] is not None else "",
                "data": str(r[5]) if r[5] is not None else None,
            }
            for r in rows
        ]
    except Exception as e:
        print("Erro ao listar histórico:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao listar histórico")
