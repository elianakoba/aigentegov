from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==========================================================
# TIPOS FIXOS
# ==========================================================

CanalOrigem = Literal["whatsapp", "web", "atendente"]

ProximaAcaoLocalizacao = Literal[
    "PROSSEGUIR_AGENDAMENTO",
    "INFORMAR_DADOS_OBRIGATORIOS",
    "ENCAMINHAR_ATENDENTE_HUMANO"
]


# ==========================================================
# REQUEST
# ==========================================================

class LocalizaCidadaoParaAgendamentoRequest(BaseModel):
    """
    Payload da etapa anterior ao agendamento.

    Esta API é responsável por:
    - localizar o cidadão por prontuário GAPD ou telefone;
    - verificar se o serviço solicitado já foi utilizado anteriormente;
    - localizar uma notificação-base válida do mesmo serviço;
    - devolver o id_notificacao_base que será usado pela API de agendamento.

    Esta rota NÃO cria agendamento.
    Ela apenas decide se o fluxo pode prosseguir para a API de agendamento.

    Regra:
    - informar pelo menos um identificador: prontuariogapd OU telefone.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "prontuariogapd": "123456",
                    "servicoespecializado": "FISIOTERAPIA",
                    "canal_origem": "whatsapp"
                },
                {
                    "telefone": "(11) 99999-8888",
                    "servicoespecializado": "TRANSPORTE",
                    "canal_origem": "web"
                }
            ]
        }
    )

    prontuariogapd: Optional[str] = Field(
        default=None,
        title="Prontuário GAPD",
        description=(
            "Prontuário do cidadão no GAPD. "
            "Informe este campo ou o telefone."
        ),
        examples=["123456"]
    )

    telefone: Optional[str] = Field(
        default=None,
        title="Telefone",
        description=(
            "Telefone do cidadão, preferencialmente o número do WhatsApp. "
            "Informe este campo ou o prontuariogapd."
        ),
        examples=["(11) 99999-8888"]
    )

    servicoespecializado: str = Field(
        ...,
        title="Serviço especializado",
        description=(
            "Serviço para o qual se deseja validar se o cidadão pode seguir "
            "para o fluxo de autoagendamento."
        ),
        examples=["FISIOTERAPIA", "TRANSPORTE"]
    )

    canal_origem: Optional[CanalOrigem] = Field(
        default=None,
        title="Canal de origem",
        description="Canal de origem da solicitação.",
        examples=["whatsapp"]
    )

    @field_validator("prontuariogapd", "telefone", mode="before")
    @classmethod
    def normalizar_texto(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @model_validator(mode="after")
    def validar_identificador_obrigatorio(self):
        if not self.prontuariogapd and not self.telefone:
            raise ValueError(
                "É obrigatório informar pelo menos um identificador: prontuariogapd ou telefone."
            )
        return self


# ==========================================================
# RESPONSE
# ==========================================================

class DadosRetornoLocalizaCidadaoParaAgendamentoResponse(BaseModel):
    cidadao_identificado: Optional[bool] = Field(
        default=None,
        description="Indica se o cidadão foi localizado com sucesso."
    )

    servico_elegivel_autoagendamento: Optional[bool] = Field(
        default=None,
        description=(
            "Indica se o serviço solicitado já foi utilizado anteriormente "
            "pelo cidadão e, portanto, pode seguir para autoagendamento."
        )
    )

    id_notificacao_base: Optional[int] = Field(
        default=None,
        description=(
            "Identificador da notificação-base do mesmo serviço. "
            "Esse campo deve ser enviado posteriormente para a API de agendamento."
        )
    )

    prontuariogapd: Optional[str] = Field(
        default=None,
        description="Prontuário identificado."
    )

    nome: Optional[str] = Field(
        default=None,
        description="Nome do cidadão identificado."
    )

    telefone: Optional[str] = Field(
        default=None,
        description="Telefone identificado."
    )

    servicoespecializado: Optional[str] = Field(
        default=None,
        description="Serviço solicitado."
    )

    tipoagenda: Optional[str] = Field(
        default=None,
        description=(
            "Tipo de agenda associado ao serviço na notificação-base encontrada. "
            "Esse dado é informativo para apoio ao fluxo."
        )
    )

    servicos_ja_utilizados: Optional[List[str]] = Field(
        default=None,
        description="Lista de serviços já encontrados no histórico do cidadão."
    )

    campos_pendentes: Optional[List[str]] = Field(
        default=None,
        description="Campos mínimos faltantes para executar a localização e validação."
    )

    @field_validator("prontuariogapd", mode="before")
    @classmethod
    def converter_prontuario_para_string(cls, value):
        if value is None:
            return value
        return str(value)


class LocalizaCidadaoParaAgendamentoResponse(BaseModel):
    sucesso: bool = Field(
        ...,
        description="Indica se a solicitação foi tratada corretamente pela API."
    )

    proxima_acao: ProximaAcaoLocalizacao = Field(
        ...,
        description=(
            "Orienta explicitamente o próximo passo do agente. "
            "Use este campo como principal referência de decisão."
        )
    )

    mensagem: str = Field(
        ...,
        description="Mensagem descritiva e objetiva do resultado."
    )

    dados: DadosRetornoLocalizaCidadaoParaAgendamentoResponse = Field(
        ...,
        description="Dados estruturados para apoiar a continuação do fluxo."
    )