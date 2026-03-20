from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class SituacaoNotificacao(str, Enum):
    NOTIFICADO = "NOTIFICADO"

class SituacaoResposta(str, Enum):
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"
    REAGENDAR = "REAGENDAR"

class NotificacaoStatusUpdate(BaseModel):
    situacaonotificacao: Optional[SituacaoNotificacao] = Field(
        default=None,
        description="Usar quando a notificação for ENVIADA ao paciente. Valor esperado: NOTIFICADO.",
        examples=["NOTIFICADO"],
    )
    observacaonotificacao: Optional[str] = Field(
        default=None,
        description="Texto livre opcional sobre o envio da notificação (ex.: canal, mensagem enviada).",
        examples=["Enviado via WhatsApp às 10:15"],
    )
    situacaoresposta: Optional[SituacaoResposta] = Field(
        default=None,
        description="Usar quando houver RESPOSTA do paciente: CONFIRMADO, CANCELADO ou REAGENDAR.",
        examples=["CONFIRMADO"],
    )
    observacaoresposta: Optional[str] = Field(
        default=None,
        description="Texto recebido do paciente (ou resumo do retorno). Obrigatório quando situacaoresposta for informado.",
        examples=["Confirmo sim", "Não vou conseguir", "Pode reagendar para amanhã?"],
    )
