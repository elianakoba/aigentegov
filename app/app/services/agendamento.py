from datetime import datetime
from typing import Optional


def gerar_protocolo() -> str:
    # MVP simples e suficiente: AAAAMMDDHHMMSS
    return datetime.now().strftime("PROTO-%Y%m%d%H%M%S")


