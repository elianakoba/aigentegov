from fastapi import APIRouter, Depends, HTTPException
from app.core.security import validar_api_key
from app.db.cidadao import ( buscar_cidadao_por_telefone,  buscar_cidadao_por_prontuario )
from app.schemas.cidadao import ( BuscarPorTelefoneRequest, BuscarPorProntuarioRequest )


router = APIRouter(
    prefix="/v1/cidadao",
    tags=["Cidadão"],
    dependencies=[Depends(validar_api_key)]
)


# ==========================================================
# IDENTIFICAR POR TELEFONE (WHATSAPP)
# ==========================================================

@router.post("/buscar-por-telefone",
            summary="Buscar cidadão pelo telefone",
            description=( "Consulta o cadastro do cidadão usando o telefone informado.\n\n"
                           "Regras importantes:\n"
                           "- O telefone deve representar o número do WhatsApp do cidadão.\n"
                           "- A API normaliza o telefone removendo caracteres não numéricos.\n"
                           "- Preferencialmente enviar no padrão E.164 (ex.: +5511999999999) ou apenas dígitos.\n\n"
                           "Uso típico:\n"
                            "- Chamado pelo Agente (WhatsApp) no início do atendimento para identificar o cidadão.\n" ),

            responses={200: {"description": "Cidadão encontrado"},
                       404: {"description": "Cidadão não encontrado"},
                       401: {"description": "Não autorizado (API Key ausente ou inválida)"},
                       422: {"description": "Erro de validação do payload"},},
             )
def identificar_por_telefone(request: BuscarPorTelefoneRequest):
    cidadao = buscar_cidadao_por_telefone(request.telefone)
    if not cidadao:
        raise HTTPException(status_code=404, detail="cidadao não encontrado")
    return cidadao


# =========================================================='
# IDENTIFICAR POR PRONTUARIO
# ==========================================================

@router.post("/buscar-por-prontuario",
             summary="Buscar cidadão pelo prontuário",
             description=( "Consulta o cadastro do cidadão usando o número de prontuário.\n\n"
                            "Regras importantes:\n"
                            "- O prontuário deve ser enviado exatamente como cadastrado (ex.: sem máscara, se não existir máscara).\n"
                            "- Se houver variações no legado (zeros à esquerda, prefixos), defina aqui a regra oficial.\n\n"
                            "Uso típico:\n"
                            "- Integrações internas (ex.: sistema legado) ou atendimento humano quando o prontuário é conhecido.\n"
                        ),
            responses={
                200: {"description": "Cidadão encontrado"},
                404: {"description": "Cidadão não encontrado"},
                401: {"description": "Não autorizado (API Key ausente ou inválida)"},
                422: {"description": "Erro de validação do payload"}, },)

def identificar_por_prontuario(request: BuscarPorProntuarioRequest):
    cidadao = buscar_cidadao_por_prontuario(request.prontuario)
    if not cidadao:
        raise HTTPException(status_code=404, detail="cidadao não encontrado")
    return cidadao
