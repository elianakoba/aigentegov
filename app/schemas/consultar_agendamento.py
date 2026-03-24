from typing import List, Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


# ==========================================================
# TIPOS FIXOS
# ==========================================================

ProximaAcaoConsultarAgendamento = Literal[
    "EXIBIR_DADOS_AGENDAMENTO",
    "ESCOLHER_PRONTUARIO",
    "INFORMAR_SEM_AGENDAMENTO",
    "INFORMAR_DADOS_OBRIGATORIOS",
    "ENCAMINHAR_ATENDENTE_HUMANO"
]


# ==========================================================
# REQUEST
# ==========================================================

class ConsultarAgendamentoRequest(BaseModel):
    """
    Payload único da API de consulta de agendamento.

    Regras:
    - O telefone é usado apenas para localizar possíveis prontuários.
    - A consulta final do agendamento é feita por prontuário.
    - Quando houver mais de um cidadão vinculado ao telefone,
      a API retorna ESCOLHER_PRONTUARIO.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telefone": "11999998888"
                },
                {
                    "telefone": "11999998888",
                    "prontuariogapd": "123456"
                },
                {
                    "prontuariogapd": "123456"
                }
            ]
        }
    )

    telefone: Optional[str] = Field(
        default=None,
        description=(
            "Telefone do cidadão. Utilizado apenas para localizar possíveis "
            "prontuários associados."
        )
    )

    prontuariogapd: Optional[str] = Field(
        default=None,
        description=(
            "Prontuário do cidadão. Quando informado, a consulta é realizada "
            "diretamente por prontuário."
        )
    )

    incluir_todos_agendamentos: bool = Field(
        default=True,
        description=(
            "Mantido por compatibilidade. Nesta consulta, quando houver agendamentos "
            "válidos, a API retornará a lista de agendamentos encontrados para o cidadão."
        )
    )


# ==========================================================
# RESPONSE
# ==========================================================

class CidadaoLocalizadoResponse(BaseModel):
    prontuariogapd: str = Field(..., description="Prontuário do cidadão localizado.")
    nome: Optional[str] = Field(default=None, description="Nome do cidadão localizado.")


class AgendamentoLocalizadoResponse(BaseModel):
    id_notificacao: int = Field(..., description="Identificador da notificação/agendamento.")
    prontuariogapd: Optional[str] = Field(default=None, description="Prontuário do cidadão.")
    nome: Optional[str] = Field(default=None, description="Nome do cidadão.")
    servicoespecializado: Optional[str] = Field(
        default=None,
        description="Serviço especializado relacionado ao agendamento."
    )
    dataagendamento: Optional[date] = Field(
        default=None,
        description="Data do agendamento."
    )
    horaagendamento: Optional[str] = Field(
        default=None,
        description="Hora do agendamento no formato HH:MM:SS."
    )
    situacaonotificacao: Optional[str] = Field(
        default=None,
        description="Situação registrada na notificação."
    )
    statusagenda: Optional[str] = Field(
        default=None,
        description="Status operacional do agendamento."
    )
    observacaonotificacao: Optional[str] = Field(
        default=None,
        description="Observação registrada para o agendamento."
    )
    origem: Optional[str] = Field(
        default=None,
        description="Origem/local de referência do agendamento, quando aplicável."
    )
    destino: Optional[str] = Field(
        default=None,
        description="Destino/local de referência do agendamento, quando aplicável."
    )


class DadosRetornoConsultarAgendamentoResponse(BaseModel):
    quantidade_cidadaos_encontrados: int = Field(
        ...,
        description="Quantidade de cidadãos localizados para o telefone informado."
    )
    cidadaos_localizados: Optional[List[CidadaoLocalizadoResponse]] = Field(
        default=None,
        description=(
            "Lista de cidadãos localizados quando houver mais de um prontuário "
            "associado ao telefone."
        )
    )
    possui_agendamento: bool = Field(
        ...,
        description="Indica se existe ao menos um agendamento válido para o cidadão."
    )
    quantidade_agendamentos_encontrados: int = Field(
        ...,
        description="Quantidade de agendamentos válidos encontrados para o cidadão consultado."
    )
    proximo_agendamento: Optional[AgendamentoLocalizadoResponse] = Field(
        default=None,
        description="Próximo agendamento válido encontrado."
    )
    agendamentos: Optional[List[AgendamentoLocalizadoResponse]] = Field(
        default=None,
        description=(
            "Lista de agendamentos válidos encontrados para o cidadão consultado. "
            "Pode haver mais de um agendamento."
        )
    )
    campos_pendentes: Optional[List[str]] = Field(
        default=None,
        description="Lista de campos obrigatórios faltantes para o fluxo continuar."
    )


class ConsultarAgendamentoResponse(BaseModel):
    sucesso: bool = Field(..., description="Indica se a solicitação foi tratada corretamente pela API.")
    proxima_acao: ProximaAcaoConsultarAgendamento = Field(
        ...,
        description="Orienta explicitamente o próximo passo do agente."
    )
    mensagem: str = Field(..., description="Mensagem descritiva do resultado.")
    dados: DadosRetornoConsultarAgendamentoResponse = Field(
        ...,
        description="Dados estruturados para apoiar a continuação do fluxo conversacional."
    )