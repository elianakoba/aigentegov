from pydantic import BaseModel, Field
from typing import Optional


class CidadaoResponse(BaseModel):
    nome: str
    prontuario: str
    telefone: str
    origem: str


class BuscarPorTelefoneRequest(BaseModel):
    telefone: str = Field(
        ...,
        description="Telefone do cidadão (DDD + TELEFONE). Pode conter +, espaços, parênteses; a API irá normalizar.",
        examples=[ "11999999999"]
    )


class BuscarPorProntuarioRequest(BaseModel):
    prontuario: str = Field(
        ...,
        description="Número de prontuário do cidadão conforme cadastro no sistema legado.",
        examples=["123456", "000123456"]
    )
