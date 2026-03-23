from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class NotificacaoResponse(BaseModel):
    id_notificacao: int
    dataagendamento: Optional[date] = None
    diadasemanaagendamento: Optional[str] = None
    horaagendamento: Optional[str] = None
    prontuariogapd: Optional[int] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    servicoespecializado: Optional[str] = None
    origem: Optional[str] = None
    destino: Optional[str] = None
    situacaonotificacao: Optional[str] = None
    datanotificacao: Optional[datetime] = None
    observacaonotificacao: Optional[str] = None
    situacaoresposta: Optional[str] = None
    dataresposta: Optional[datetime] = None
    observacaoresposta: Optional[str] = None

    class Config:
        from_attributes = True