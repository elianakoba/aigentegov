from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# 🔹 ESTE OBJETO CRIA O SCHEMA DE SEGURANÇA
security = HTTPBearer(auto_error=False)

def validar_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Valida API Key enviada no header Authorization.
    Formato: Authorization: Bearer <API_KEY>
    """

    #  Header não enviado
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization não informado",
        )

    token = credentials.credentials

    #  API_KEY não configurada
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY não configurada no servidor",
        )

    #  Token inválido
    if token != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
        )

    return True
