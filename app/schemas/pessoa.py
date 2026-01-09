from pydantic import BaseModel, Field

class ConsultaTelefoneRequest(BaseModel):
    telefone: str = Field(
        ...,
        example="(11) 98625-7349",
        description="Telefone obtido na conversa via WhatsApp."
    )

class PessoaResponse(BaseModel):
    cpf: str | None = Field(default=None, example="12345678900")
    nome: str = Field(..., example="Maria da Silva")
    datanascimento: str | None = Field(default=None, example="1999-05-20")
    telefone: str | None = Field(default=None, example="11986257349")
    id_pessoa: str | None = Field(default=None, example="1234")
