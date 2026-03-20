from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class NotificacaoResponse(BaseModel):
    id_notificacao: int
    dataagendamento: Optional[date]
    horaagendamento: Optional[str]
    prontuariogapd: Optional[int]
    nome: Optional[str]
    telefone: Optional[str]
    servicoespecializado: Optional[str]
    origem: Optional[str]
    destino: Optional[str]
    situacaonotificacao: Optional[str]
    datanotificacao: Optional[datetime]
    observacaonotificacao: Optional[str]
    situacaoresposta: Optional[str]
    dataresposta: Optional[datetime]
    observacaoresposta: Optional[str]

    class Config:
        from_attributes = True

