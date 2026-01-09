from fastapi import APIRouter, HTTPException, Depends
from app.core.security import require_api_key
from app.core.phone import normalize_phone
from app.schemas.pessoa import ConsultaTelefoneRequest, PessoaResponse
from app.db.sqlserver import buscar_pessoa_por_telefone

router = APIRouter(
    prefix="/v1/sdpd",
    tags=["SDPD - Consulta Pessoa"],
    dependencies=[Depends(require_api_key)]
)

@router.post(
    "/consultar-telefone",
    response_model=PessoaResponse,
    summary="Consultar pessoa por telefone",
    description="Consulta dados da pessoa no SQL Server (legado) a partir do telefone obtido via WhatsApp."
)
def consultar_telefone(payload: ConsultaTelefoneRequest):
    telefone_norm = normalize_phone(payload.telefone)

    # Validação mínima após normalização:
    # - com DDD: 10 (fixo) ou 11 (celular)
    if not telefone_norm.isdigit() or len(telefone_norm) not in (10, 11):
        raise HTTPException(status_code=400, detail="Telefone inválido")

    try:
        row = buscar_pessoa_por_telefone(payload.telefone)
        if not row:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        # Usar índices é mais robusto do que nomes (pyodbc.Row pode variar)
        cpf = row[0]
        nome = row[1]
        datanascimento = row[2]
        id_pessoa = row[3]
        telefone_db = row[4] if len(row) > 4 else None
        

        return {
            "cpf": str(cpf) if cpf is not None else None,
            "nome": str(nome) if nome is not None else "",
            "datanascimento": str(datanascimento) if datanascimento else None,
            "telefone": str(telefone_db) if telefone_db else telefone_norm,
            "id_pessoa": str(id_pessoa) if id_pessoa else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("Erro ao consultar banco:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao consultar banco")
