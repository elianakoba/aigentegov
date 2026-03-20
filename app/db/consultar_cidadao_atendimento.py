import re
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


# ==========================================================
# NORMALIZAÇÃO
# ==========================================================

def normalizar_somente_digitos(valor: str | None) -> str | None:
    if not valor:
        return None
    digitos = re.sub(r"\D", "", valor)
    return digitos or None


def normalizar_servico(valor: str | None) -> str | None:
    if not valor:
        return None
    return valor.strip().upper()


# ==========================================================
# LOCALIZAÇÃO DO CIDADÃO
# ==========================================================

def buscar_cidadao_por_identificadores(
    prontuariogapd: str | None,
    telefone: str | None
):
    """
    Localiza o cidadão na tabela notificacao com base em:
    - prontuário
    - telefone

    Estratégia:
    - usa os identificadores fornecidos para encontrar um registro confiável;
    - retorna o registro mais recente encontrado.
    """
    prontuariogapd_norm = prontuariogapd.strip() if prontuariogapd else None
    telefone_norm = normalizar_somente_digitos(telefone)

    filtros = []
    params = []

    if prontuariogapd_norm:
        filtros.append("prontuariogapd = %s")
        params.append(prontuariogapd_norm)

    if telefone_norm:
        filtros.append("regexp_replace(COALESCE(telefone, ''), '\\D', '', 'g') = %s")
        params.append(telefone_norm)

    if not filtros:
        return None

    query = f"""
        SELECT
            id_notificacao,
            prontuariogapd,
            nome,
            telefone,
            servicoespecializado,
            tipoagenda,
            datanotificacao
        FROM notificacao
        WHERE {" OR ".join(filtros)}
        ORDER BY datanotificacao DESC NULLS LAST, id_notificacao DESC
        LIMIT 1
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        conn.close()


# ==========================================================
# HISTÓRICO DE SERVIÇOS DO CIDADÃO
# ==========================================================

def buscar_servicos_ja_utilizados_cidadao(
    prontuariogapd: str | None,
    telefone: str | None
) -> list[str]:
    """
    Retorna a lista de serviços já utilizados pelo cidadão.

    Nesta POC, usa a própria tabela notificacao como base histórica.
    """
    prontuariogapd_norm = prontuariogapd.strip() if prontuariogapd else None
    telefone_norm = normalizar_somente_digitos(telefone)

    filtros = []
    params = []

    if prontuariogapd_norm:
        filtros.append("prontuariogapd = %s")
        params.append(prontuariogapd_norm)

    if telefone_norm:
        filtros.append("regexp_replace(COALESCE(telefone, ''), '\\D', '', 'g') = %s")
        params.append(telefone_norm)

    if not filtros:
        return []

    query = f"""
        SELECT DISTINCT servicoespecializado
        FROM notificacao
        WHERE servicoespecializado IS NOT NULL
          AND ({' OR '.join(filtros)})
          AND COALESCE(statusagenda, '') IN (
                'AGENDADO',
                'AUTORIZADO',
                'CONCLUIDO'
          )
        ORDER BY servicoespecializado
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            registros = cur.fetchall()
            return [r["servicoespecializado"] for r in registros if r.get("servicoespecializado")]
    finally:
        conn.close()


# ==========================================================
# ÚLTIMO REGISTRO RELEVANTE DO CIDADÃO
# ==========================================================

def buscar_ultimo_registro_relevante_cidadao(
    prontuariogapd: str | None,
    telefone: str | None
):
    """
    Busca o registro mais recente do cidadão na tabela notificacao.
    Pode ser usado para apoio ao atendimento quando a intenção for
    apenas consultar dados gerais do cidadão.
    """
    prontuariogapd_norm = prontuariogapd.strip() if prontuariogapd else None
    telefone_norm = normalizar_somente_digitos(telefone)

    filtros = []
    params = []

    if prontuariogapd_norm:
        filtros.append("prontuariogapd = %s")
        params.append(prontuariogapd_norm)

    if telefone_norm:
        filtros.append("regexp_replace(COALESCE(telefone, ''), '\\D', '', 'g') = %s")
        params.append(telefone_norm)

    if not filtros:
        return None

    query = f"""
        SELECT
            id_notificacao,
            servicoespecializado,
            tipoagenda,
            origem,
            destino,
            situacaonotificacao,
            statusagenda,
            datanotificacao
        FROM notificacao
        WHERE {" OR ".join(filtros)}
        ORDER BY datanotificacao DESC NULLS LAST, id_notificacao DESC
        LIMIT 1
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        conn.close()


# ==========================================================
# NOTIFICAÇÃO-BASE DO SERVIÇO SOLICITADO
# ==========================================================

def buscar_notificacao_base_servico(
    prontuariogapd: str | None,
    telefone: str | None,
    servicoespecializado: str
):
    """
    Busca a notificação-base mais recente do mesmo serviço solicitado.

    Essa notificação-base é a melhor candidata para ser usada em fluxos
    que exigem continuidade de atendimento.
    """
    prontuariogapd_norm = prontuariogapd.strip() if prontuariogapd else None
    telefone_norm = normalizar_somente_digitos(telefone)
    servico_norm = normalizar_servico(servicoespecializado)

    filtros_identificacao = []
    params = []

    if prontuariogapd_norm:
        filtros_identificacao.append("prontuariogapd = %s")
        params.append(prontuariogapd_norm)

    if telefone_norm:
        filtros_identificacao.append("regexp_replace(COALESCE(telefone, ''), '\\D', '', 'g') = %s")
        params.append(telefone_norm)

    if not filtros_identificacao:
        return None

    query = f"""
        SELECT
            id_notificacao,
            prontuariogapd,
            nome,
            telefone,
            servicoespecializado,
            tipoagenda,
            origem,
            destino,
            datanotificacao,
            situacaonotificacao,
            statusagenda
        FROM notificacao
        WHERE UPPER(TRIM(servicoespecializado)) = %s
          AND ({' OR '.join(filtros_identificacao)})
          AND COALESCE(statusagenda, '') IN (
                'AGENDADO',
                'AUTORIZADO',
                'CONCLUIDO'
          )
        ORDER BY datanotificacao DESC NULLS LAST, id_notificacao DESC
        LIMIT 1
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, [servico_norm] + params)
            return cur.fetchone()
    finally:
        conn.close()