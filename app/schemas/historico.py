from pydantic import BaseModel, Field
from typing import Optional

class CriarHistoricoRequest(BaseModel):
    id_pessoa: int = Field(..., ge=1, description="ID da pessoa no legado (pessoa.id_pessoa)")
    historico: str = Field(..., min_length=1, max_length=1000, description="Texto do histórico")
    tipo_historico: Optional[int] = Field(default=None, ge=1, le=6, description="vet_TipoHistorico (tinyint)")
    id_usuario: Optional[int] = Field(default=None, ge=1, description="ID do usuário (opcional)")

class CriarHistoricoResponse(BaseModel):
    id_historico: int = Field(..., description="Id_HistoricoSDPD gerado")
    id_pessoa: int
    id_usuario: Optional[int] = None
    tipo_historico: Optional[int] = None
    historico: str
    data: str = Field(..., description="Data/hora de gravação (GETDATE do SQL Server)")
