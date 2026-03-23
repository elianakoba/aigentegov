from fastapi import APIRouter, HTTPException

from app.db.consultar_agendamento import consultar_agendamento
from app.schemas.consultar_agendamento import (
    ConsultarAgendamentoRequest,
    ConsultarAgendamentoResponse,
)

router = APIRouter(
    prefix="/v1/consultar_agendamento",
    tags=["Consultar Agendamento"],
)


@router.post(
    "",
    response_model=ConsultarAgendamentoResponse,
    summary="Consultar se o cidadão possui agendamento e qual o status",
    description=(
        "API para consulta de agendamento do cidadão a partir da data atual.\n\n"
        "Regras desta API:\n"
        "1. O telefone é utilizado apenas para localizar possíveis prontuários associados.\n"
        "2. A consulta final do agendamento é realizada por prontuariogapd.\n"
        "3. Quando o telefone localizar mais de um cidadão, a API retorna `ESCOLHER_PRONTUARIO`.\n"
        "4. Quando informado diretamente o prontuariogapd, a consulta é executada de forma direta.\n"
        "5. Apenas agendamentos com `dataagendamento >= data atual` são considerados nesta consulta.\n\n"
        "Interpretação do campo proxima_acao:\n"
        "- `EXIBIR_DADOS_AGENDAMENTO`: existe agendamento válido e o agente pode apresentar os dados.\n"
        "- `ESCOLHER_PRONTUARIO`: o telefone informado está associado a mais de um prontuário.\n"
        "- `INFORMAR_SEM_AGENDAMENTO`: o prontuário foi identificado, mas não há agendamento válido a partir da data atual.\n"
        "- `INFORMAR_DADOS_OBRIGATORIOS`: faltam campos obrigatórios para a consulta.\n"
        "- `ENCAMINHAR_ATENDENTE_HUMANO`: não foi possível concluir a identificação de forma segura."
    ),
    responses={
        200: {"description": "Consulta processada com sucesso."},
        500: {"description": "Erro interno ao processar a consulta."},
    },
)
def post_consultar_agendamento(
    dados_entrada: ConsultarAgendamentoRequest,
) -> ConsultarAgendamentoResponse:
    try:
        return consultar_agendamento(dados_entrada.model_dump())

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao consultar agendamento: {str(exc)}",
        ) from exc