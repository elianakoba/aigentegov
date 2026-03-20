from pydantic import BaseModel
from typing import Optional


class NotificacaoStatusUpdate(BaseModel):
    # ENVIO
    situacaonotificacao: Optional[str] = None
    observacaonotificacao: Optional[str] = None

    # RESPOSTA
    situacaoresposta: Optional[str] = None
    observacaoresposta: Optional[str] = None
