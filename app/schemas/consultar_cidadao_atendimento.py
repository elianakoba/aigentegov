from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==========================================================
# TIPOS FIXOS
# ==========================================================

CanalOrigem = Literal["whatsapp", "web", "atendente"]

IntencaoConsultaCidadaoAtendimento = Literal[
    "CONSULTAR_DADOS_CIDADAO",
    "VALIDAR_CONTINUIDADE_ATENDIMENTO"
]

ProximaAcaoConsultaCidadaoAtendimento = Literal[
    "EXIBIR_DADOS_CIDADAO",
    "PROSSEGUIR_ATENDIMENTO",
    "INFORMAR_DADOS_OBRIGATORIOS",
    "ENCAMINHAR_ATENDENTE_HUMANO"
]


# ==========================================================
# REQUEST
# ==========================================================

class ConsultarCidadaoAtendimentoRequest(BaseModel):
    """
    Payload da API de consulta do cidadão para atendimento.

    Objetivo:
    - localizar o cidadão por prontuário GAPD ou telefone;
    - consultar dados básicos do cidadão para apoio ao atendimento;
    - validar continuidade do atendimento, quando essa for a intenção;
    - retornar as informações necessárias para orientar o próximo passo do agente.

    Regras de preenchimento:
    - é obrigatório informar pelo menos um identificador:
      prontuariogapd OU telefone;
    - quando a intencao for VALIDAR_CONTINUIDADE_ATENDIMENTO,
      o campo servicoespecializado torna-se obrigatório.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "telefone": "(11) 99999-8888",
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "whatsapp"
                },
                {
                    "prontuariogapd": "123456",
                    "servicoespecializado": "FISIOTERAPIA",
                    "intencao": "VALIDAR_CONTINUIDADE_ATENDIMENTO",
                    "canal_origem": "whatsapp"
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

    intencao: IntencaoConsultaCidadaoAtendimento = Field(
        ...,
        title="Intenção da consulta",
        description=(
            "Objetivo da consulta, que direciona o comportamento da API. "
            "Valores aceitos: CONSULTAR_DADOS_CIDADAO ou VALIDAR_CONTINUIDADE_ATENDIMENTO."
        ),
        examples=["CONSULTAR_DADOS_CIDADAO"]
    )

    servicoespecializado: Optional[str] = Field(
        default=None,
        title="Serviço especializado",
        description=(
            "Serviço para o qual se deseja validar a continuidade do atendimento. "
            "Obrigatório somente quando a intencao for VALIDAR_CONTINUIDADE_ATENDIMENTO."
        ),
        examples=["FISIOTERAPIA", "TRANSPORTE"]
    )

    canal_origem: Optional[CanalOrigem] = Field(
        default=None,
        title="Canal de origem",
        description="Canal de origem da solicitação.",
        examples=["whatsapp"]
    )

    @field_validator("prontuariogapd", "telefone", "servicoespecializado", mode="before")
    @classmethod
    def normalizar_texto(cls, value):
        if value is None:
            return value
        return str(value).strip()


# ==========================================================
# RESPONSE
# ==========================================================

class DadosRetornoConsultarCidadaoAtendimentoResponse(BaseModel):
    cidadao_identificado: Optional[bool] = Field(
        default=None,
        description="Indica se o cidadão foi localizado com sucesso."
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

    intencao: Optional[IntencaoConsultaCidadaoAtendimento] = Field(
        default=None,
        description="Intenção de consulta recebida na requisição."
    )

    servicoespecializado: Optional[str] = Field(
        default=None,
        description="Serviço informado na consulta, quando aplicável."
    )

    servicos_ja_utilizados: Optional[List[str]] = Field(
        default=None,
        description="Lista de serviços já encontrados no histórico do cidadão."
    )

    continuidade_atendimento: Optional[bool] = Field(
        default=None,
        description=(
            "Indica se há continuidade possível no atendimento, "
            "quando a intenção for VALIDAR_CONTINUIDADE_ATENDIMENTO."
        )
    )

    id_notificacao_base: Optional[int] = Field(
        default=None,
        description="Identificador do registro-base relacionado ao atendimento, quando aplicável."
    )

    tipoagenda: Optional[str] = Field(
        default=None,
        description="Tipo de agenda associado ao registro-base encontrado, quando aplicável."
    )

    ultimo_servicoespecializado: Optional[str] = Field(
        default=None,
        description="Último serviço encontrado no histórico do cidadão."
    )

    ultima_situacaonotificacao: Optional[str] = Field(
        default=None,
        description="Última situação de notificação encontrada para o cidadão."
    )

    ultimo_statusagenda: Optional[str] = Field(
        default=None,
        description="Último statusagenda encontrado para o cidadão."
    )

    campos_pendentes: Optional[List[str]] = Field(
        default=None,
        description=(
            "Lista de campos obrigatórios faltantes para executar a consulta. "
            "Exemplo: ['servicoespecializado'] quando a intenção exigir esse campo."
        )
    )

    @field_validator("prontuariogapd", mode="before")
    @classmethod
    def converter_prontuario_para_string(cls, value):
        if value is None:
            return value
        return str(value)


class ConsultarCidadaoAtendimentoResponse(BaseModel):
    sucesso: bool = Field(
        ...,
        description="Indica se a solicitação foi tratada corretamente pela API."
    )

    proxima_acao: ProximaAcaoConsultaCidadaoAtendimento = Field(
        ...,
        description=(
            "Orienta explicitamente o próximo passo do agente.\n"
            "- EXIBIR_DADOS_CIDADAO: cidadão localizado e dados disponíveis para consulta.\n"
            "- PROSSEGUIR_ATENDIMENTO: continuidade de atendimento validada com sucesso.\n"
            "- INFORMAR_DADOS_OBRIGATORIOS: faltam campos para processar a intenção informada.\n"
            "- ENCAMINHAR_ATENDENTE_HUMANO: não foi possível automatizar a continuidade do atendimento."
        )
    )

    mensagem: str = Field(
        ...,
        description="Mensagem descritiva e objetiva do resultado."
    )

    dados: DadosRetornoConsultarCidadaoAtendimentoResponse = Field(
        ...,
        description="Dados estruturados para apoiar a continuação do fluxo."
    )