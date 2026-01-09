import os
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

API_KEY = os.getenv("API_KEY")  # se não existir, endpoints podem ficar sem proteção por enquanto
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(api_key: str = Security(api_key_header)):
    # Se não configurou API_KEY ainda, não bloqueia (modo dev).
    if not API_KEY:
        return

    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
