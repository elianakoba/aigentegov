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
    "ENCAMINHAR_ATENDENTE_HUMANO",
    "SELECIONAR_CIDADAO"
]


# ==========================================================
# REQUEST
# ==========================================================

class ConsultarCidadaoAtendimentoRequest(BaseModel):
    """
    Payload da API de consulta do cidadão para atendimento.

    Objetivos suportados:
    - CONSULTAR_DADOS_CIDADAO:
      localizar o cidadão e retornar apenas sua identificação básica.
    - VALIDAR_CONTINUIDADE_ATENDIMENTO:
      verificar se existe registro anterior do serviço solicitado para o cidadão
      e se o statusagenda desse registro permite continuidade automática.

    Regras de preenchimento:
    - é obrigatório informar pelo menos um identificador:
      prontuariogapd OU telefone;
    - quando a intencao for VALIDAR_CONTINUIDADE_ATENDIMENTO,
      o campo servicoespecializado torna-se obrigatório;
    - o canal_origem é opcional e serve apenas para contexto da integração.
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
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "atendente"
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
            "Este é o identificador prioritário quando disponível. "
            "Informe este campo ou o telefone."
        ),
        examples=["123456"]
    )

    telefone: Optional[str] = Field(
        default=None,
        title="Telefone",
        description=(
            "Telefone do cidadão, preferencialmente o número do WhatsApp. "
            "Pode localizar mais de um cidadão quando houver compartilhamento do número "
            "entre responsável e dependentes. Informe este campo ou o prontuariogapd."
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
            "Serviço para o qual se deseja validar continuidade do atendimento. "
            "Obrigatório somente quando a intencao for VALIDAR_CONTINUIDADE_ATENDIMENTO."
        ),
        examples=["FISIOTERAPIA", "TRANSPORTE"]
    )

    canal_origem: Optional[CanalOrigem] = Field(
        default=None,
        title="Canal de origem",
        description=(
            "Canal de origem da solicitação. "
            "Campo opcional, usado apenas para contexto da integração."
        ),
        examples=["whatsapp"]
    )

    @field_validator("prontuariogapd", "telefone", "servicoespecializado", mode="before")
    @classmethod
    def normalizar_texto(cls, value):
        if value is None:
            return value
        return str(value).strip()


# ==========================================================
# MODELO DE CIDADÃO ENCONTRADO
# ==========================================================

class CidadaoEncontradoOption(BaseModel):
    prontuariogapd: Optional[str] = Field(
        default=None,
        description="Prontuário GAPD do cidadão encontrado."
    )

    nome: Optional[str] = Field(
        default=None,
        description="Nome do cidadão encontrado."
    )

    telefone: Optional[str] = Field(
        default=None,
        description="Telefone associado ao cidadão encontrado."
    )

    @field_validator("prontuariogapd", "nome", "telefone", mode="before")
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
        description="Indica se o cidadão foi identificado com sucesso."
    )

    multiplicidade_cidadaos: Optional[bool] = Field(
        default=None,
        description="Indica se mais de um cidadão foi encontrado para os identificadores informados."
    )

    quantidade_cidadaos_encontrados: Optional[int] = Field(
        default=None,
        description="Quantidade de cidadãos distintos encontrados."
    )

    cidadaos_encontrados: Optional[List[CidadaoEncontradoOption]] = Field(
        default=None,
        description=(
            "Lista de cidadãos encontrados quando houver mais de uma pessoa vinculada "
            "ao mesmo telefone e for necessário selecionar para prosseguir."
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

    intencao: Optional[IntencaoConsultaCidadaoAtendimento] = Field(
        default=None,
        description="Intenção recebida na requisição."
    )

    servicoespecializado: Optional[str] = Field(
        default=None,
        description="Serviço informado na consulta, quando aplicável."
    )

    continuidade_atendimento: Optional[bool] = Field(
        default=None,
        description=(
            "Indica se existe continuidade automática válida para o serviço solicitado."
        )
    )

    id_notificacao_base: Optional[int] = Field(
        default=None,
        description="Identificador do registro-base válido para continuidade, quando aplicável."
    )

    tipoagenda: Optional[str] = Field(
        default=None,
        description="Tipo de agenda do registro-base encontrado, quando aplicável."
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
            "- EXIBIR_DADOS_CIDADAO: cidadão identificado e dados básicos disponíveis.\n"
            "- PROSSEGUIR_ATENDIMENTO: continuidade validada com sucesso.\n"
            "- INFORMAR_DADOS_OBRIGATORIOS: faltam campos obrigatórios para processar a solicitação.\n"
            "- ENCAMINHAR_ATENDENTE_HUMANO: não foi possível automatizar o atendimento.\n"
            "- SELECIONAR_CIDADAO: foi encontrado mais de um cidadão vinculado ao telefone informado."
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