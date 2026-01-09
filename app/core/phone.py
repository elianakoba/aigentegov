import re
from typing import List

DEFAULT_DDD = "11"

def _digits_only(value: str) -> str:
    """Remove tudo que não for número."""
    return re.sub(r"\D+", "", value or "")

def normalize_phone(raw: str, default_ddd: str = DEFAULT_DDD) -> str:
    """
    Normaliza telefone para um formato canônico numérico.

    Regras:
    - remove caracteres especiais ((), -, espaços, + etc.)
    - se começar com 011, remove o 0 inicial (011xxxxxxxx -> 11xxxxxxxx)
    - se tiver 8 dígitos (fixo sem DDD), assume DDD = 11
    - se tiver 9 dígitos (celular sem DDD), assume DDD = 11
    """
    d = _digits_only(raw)

    # Remove prefixo 0 de discagem antiga (011...)
    if d.startswith("0") and len(d) >= 3:
        # Ex.: 011950268172 -> 11950268172
        d = d[1:]

    # Sem DDD (8 dígitos fixo)
    if len(d) == 8:
        d = default_ddd + d

    # Sem DDD (9 dígitos celular)
    if len(d) == 9:
        d = default_ddd + d

    return d

def candidate_phones_for_lookup(raw: str, default_ddd: str = DEFAULT_DDD) -> List[str]:
    """
    Gera uma lista de candidatos prováveis para busca no legado.

    Estratégia:
    - tenta o normalizado (com DDD quando aplicável)
    - tenta o somente dígitos original (às vezes o legado guarda "sujo")
    - se normalizado tem DDD, também tenta sem DDD (caso a base esteja sem DDD)
    - se começou com 0 e removemos, tenta também com 0 (base legada inconsistente)
    """
    base = _digits_only(raw)
    norm = normalize_phone(raw, default_ddd=default_ddd)

    candidates: List[str] = []
    for v in [norm, base]:
        if v and v not in candidates:
            candidates.append(v)

    # Se norm tem DDD (10 ou 11), tenta também sem DDD (8 ou 9)
    if len(norm) in (10, 11):
        no_ddd = norm[2:]
        if no_ddd not in candidates:
            candidates.append(no_ddd)

    # Se tinha 0 na frente, tenta manter (caso legado guarde com 0)
    if base.startswith("0") and base not in candidates:
        candidates.append(base)

    return candidates
