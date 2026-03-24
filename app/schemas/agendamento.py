from typing import List, Literal, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


# ==========================================================
# TIPOS FIXOS
# ==========================================================

TipoAgenda = Literal["evento_variavel", "slot_fixo"]
CanalOrigem = Literal["whatsapp", "web", "atendente"]

StatusAgenda = Literal[
    "SOLICITADO",
    "AUTORIZADO",
    "AGENDADO",
    "CONCLUIDO",
    "NEGADO",
    "CANCELADO"
]

ProximaAcao = Literal[
    "AGENDAMENTO_REGISTRADO",
    "AGENDAMENTO_REALIZADO",
    "SELECIONAR_OPCAO_DISPONIVEL",
    "INFORMAR_DADOS_OBRIGATORIOS",
    "SEM_DISPONIBILIDADE",
    "ENCAMINHAR_ATENDENTE_HUMANO"
]


# ==========================================================
# REQUEST
# ==========================================================

class AgendamentoRequest(BaseModel):
    """
    Payload único da API de agendamento.

    Esta API NÃO localiza o cidadão do zero.
    Ela pressupõe que uma etapa anterior já identificou o cidadão
    por telefone, CPF ou prontuário, validou a elegibilidade
    e retornou uma notificação-base confiável.

    O campo id_notificacao_base representa essa notificação-base.
    Quando o fluxo exigir registro, a API cria uma nova linha
    em notificacao para a solicitação ou para o agendamento confirmado.
    """

    model_config = ConfigDict()

    id_notificacao_base: int = Field(
        ...,
        description=(
            "Identificador obrigatório da notificação-base previamente localizada "
            "pela etapa de identificação do cidadão. Sem esse identificador, "
            "o fluxo de agendamento não deve ser iniciado."
        )
    )

    servicoespecializado: Optional[str] = Field(
        default=None,
        description=(
            "Serviço solicitado para o novo agendamento. "
            "Quando não informado, a API tentará usar o serviço disponível na notificação-base."
        )
    )

    dataagendamento: Optional[date] = Field(
        default=None,
        description=(
            "Data efetivamente confirmada para o agendamento. "
            "Esse campo deve ser preenchido apenas quando houver confirmação real do agendamento. "
            "No fluxo conversacional normal, o agente não precisa enviá-lo para solicitar atendimento."
        )
    )

    horaagendamento: Optional[str] = Field(
        default=None,
        description=(
            "Hora efetivamente confirmada para o agendamento no formato HH:MM. "
            "Esse campo deve ser preenchido apenas quando houver confirmação real do agendamento."
        ),
        examples=["08:00", "09:30"],
        pattern=r"^\d{2}:\d{2}$"
    )

    datapreferencia: Optional[date] = Field(
        default=None,
        description=(
            "Data de preferência informada pelo cidadão para o atendimento. "
            "É usada para registrar a solicitação e para consulta de disponibilidade em slot_fixo."
        )
    )

    horapreferencia: Optional[str] = Field(
        default=None,
        description=(
            "Hora de preferência informada pelo cidadão no formato HH:MM. "
            "É usada para registrar a solicitação e pode servir como filtro preferencial em slot_fixo."
        ),
        examples=["08:00", "09:30"],
        pattern=r"^\d{2}:\d{2}$"
    )

    datasolicitacao: Optional[datetime] = Field(
        default=None,
        description=(
            "Data e hora em que a solicitação foi formalmente registrada. "
            "Quando não informada, a API assume o momento atual."
        )
    )

    dataautorizacao: Optional[datetime] = Field(
        default=None,
        description=(
            "Data e hora da autorização da solicitação, quando aplicável."
        )
    )

    origem: Optional[str] = Field(
        default=None,
        description="Origem informada para o atendimento/agendamento, quando aplicável."
    )

    destino: Optional[str] = Field(
        default=None,
        description="Destino informado para o atendimento/agendamento, quando aplicável."
    )

    id_slot: Optional[int] = Field(
        default=None,
        description=(
            "Identificador do slot escolhido pelo cidadão. "
            "Deve ser enviado apenas quando o serviço for do tipo slot_fixo "
            "e o cidadão já tiver selecionado uma opção devolvida pela API."
        )
    )

    observacaonotificacao: Optional[str] = Field(
        default=None,
        description="Observação complementar para registro operacional."
    )


# ==========================================================
# RESPONSE
# ==========================================================

class OpcaoDisponivelResponse(BaseModel):
    id_slot: int = Field(..., description="Identificador único do slot disponível.")
    dataagendamento: date = Field(..., description="Data disponível para o agendamento.")
    horaagendamento: str = Field(..., description="Horário disponível no formato HH:MM.")
    unidade: Optional[str] = Field(default=None, description="Unidade de atendimento do slot.")
    servicoespecializado: str = Field(..., description="Serviço associado ao slot.")


class DadosRetornoAgendamentoResponse(BaseModel):
    id_notificacao_base: Optional[int] = Field(default=None, description="ID da notificação-base consultada.")
    id_notificacao_agendamento: Optional[int] = Field(default=None, description="ID da nova notificação criada para a solicitação ou para o agendamento.")
    tipoagenda: Optional[TipoAgenda] = Field(default=None, description="Tipo de agenda associado ao serviço.")
    situacaonotificacao: Optional[str] = Field(default=None, description="Situação atual registrada na nova notificação.")
    statusagenda: Optional[StatusAgenda] = Field(default=None, description="Estado atual da solicitação/agendamento.")
    dataagendamento: Optional[date] = Field(default=None, description="Data efetivamente confirmada para o agendamento, quando houver.")
    horaagendamento: Optional[str] = Field(default=None, description="Hora efetivamente confirmada para o agendamento, quando houver.")
    datapreferencia: Optional[date] = Field(default=None, description="Data de preferência informada pelo cidadão.")
    horapreferencia: Optional[str] = Field(default=None, description="Hora de preferência informada pelo cidadão no formato HH:MM.")
    datasolicitacao: Optional[datetime] = Field(default=None, description="Data e hora da solicitação.")
    dataautorizacao: Optional[datetime] = Field(default=None, description="Data e hora da autorização, quando houver.")
    origem: Optional[str] = Field(default=None, description="Origem registrada.")
    destino: Optional[str] = Field(default=None, description="Destino registrado.")
    id_slot: Optional[int] = Field(default=None, description="Slot efetivamente reservado, se houver.")
    opcoes_disponiveis: Optional[List[OpcaoDisponivelResponse]] = Field(
        default=None,
        description="Lista de opções disponíveis para o cidadão escolher."
    )
    campos_pendentes: Optional[List[str]] = Field(
        default=None,
        description="Lista de campos obrigatórios faltantes para o fluxo continuar."
    )


class AgendamentoResponse(BaseModel):
    sucesso: bool = Field(..., description="Indica se a solicitação foi tratada corretamente pela API.")
    proxima_acao: ProximaAcao = Field(
        ...,
        description="Orienta explicitamente o próximo passo do agente."
    )
    mensagem: str = Field(..., description="Mensagem descritiva do resultado.")
    dados: DadosRetornoAgendamentoResponse = Field(
        ...,
        description="Dados estruturados para apoiar a continuação do fluxo conversacional."
    )