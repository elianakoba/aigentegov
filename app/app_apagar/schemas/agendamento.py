from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime



StatusAgendamento = Literal[
    "SOLICITADO",
    "CONFIRMADO",
    "CANCELADO",
    "REAGENDADO",
    "CONCLUIDO",
    "NAO_PERMITE_IA",
    "ENCAMINHADO_HUMANO",
]

TipoAgendamento = Literal["FIXO", "VARIAVEL"]
PeriodoPreferencial = Optional[Literal["MANHA", "TARDE", "NOITE"]]


class AgendamentoVariavelCreateRequest(BaseModel):
    # Cidadão
    prontuariogapd: Optional[int] = None
    nome: Optional[str] = Field(default=None, max_length=150)
    telefone: str = Field(..., max_length=50)
    cpf: Optional[str] = Field(default=None, max_length=14)

    # Serviço
    servico_id: Optional[int] = None
    servicoespecializado: Optional[str] = Field(default=None, max_length=120)
    permite_agente_ia: bool = False

    # Preferências (variável)
    #data_preferencia_inicio: Optional[str] = None  # "YYYY-MM-DD"
    #data_preferencia_fim: Optional[str] = None     # "YYYY-MM-DD"
    data_preferencia_inicio: Optional[datetime] = None
    data_preferencia_fim: Optional[datetime] = None
    diasemana: Optional[int] = Field(default=None, ge=0, le=6)
    periodo_preferencial: PeriodoPreferencial = None

    # Transporte (quando aplicável)
    origem: Optional[str] = Field(default=None, max_length=80)
    destino: Optional[str] = Field(default=None, max_length=80)

    # Rastreabilidade 
    canal: str = Field(default="WHATSAPP", max_length=20)
    solicitado_por: str = Field(default="AGENTE_IA", max_length=50)
    conversa_id: Optional[str] = Field(default=None, max_length=80)
    mensagem_id: Optional[str] = Field(default=None, max_length=80)
   
    # Outros
    observacao: Optional[str] = None


class AgendamentoResponse(BaseModel):
    id_agendamento: int
    tipo_agendamento: TipoAgendamento
    status: StatusAgendamento
    motivo_status: Optional[str] = None
    status_atualizado_em: Optional[datetime] = None

    # Datas efetivas (podem ser null no variavel)
    #inicio_em: Optional[str] = None
    #fim_em: Optional[str] = None
    inicio_em: Optional[datetime] = None
    fim_em: Optional[datetime] = None

    # Preferências
    #data_preferencia_inicio: Optional[str] = None
    #data_preferencia_fim: Optional[str] = None
    data_agendamento: Optional[datetime] = None
    data_preferencia_inicio: Optional[datetime] = None
    data_preferencia_fim: Optional[datetime] = None
    diasemana: Optional[int] = None
    periodo_preferencial: PeriodoPreferencial = None

    # Cidadão
    prontuariogapd: Optional[int] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cpf: Optional[str] = None

    # Serviço
    servico_id: Optional[int] = None
    servicoespecializado: Optional[str] = None
    permite_agente_ia: bool

    # Transporte
    origem: Optional[str] = None
    destino: Optional[str] = None

    # Rastreabilidade
    canal: str
    solicitado_por: str
    conversa_id: Optional[str] = None
    mensagem_id: Optional[str] = None

    observacao: Optional[str] = None
    ativo: bool