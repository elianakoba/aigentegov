import re
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


# ==========================================================
# CONFIGURAÇÃO DE STATUS ELEGÍVEIS
# ==========================================================

STATUS_ELEGIVEIS_CONTINUIDADE = {"AGENDADO"}


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


def normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


# ==========================================================
# FILTRO DE IDENTIFICAÇÃO PRIORITÁRIO
# ==========================================================

def _montar_filtro_identificacao_prioritario(
    prontuariogapd: str | None,
    telefone: str | None
):
    """
    Regra de identificação:

    - se houver prontuário, usar somente prontuário;
    - senão, usar telefone.

    Essa estratégia evita misturar registros de pessoas diferentes quando
    o telefone é compartilhado entre responsável e dependentes.
    """
    prontuariogapd_norm = normalizar_texto(prontuariogapd)
    telefone_norm = normalizar_somente_digitos(telefone)

    if prontuariogapd_norm:
        return "prontuariogapd = %s", [prontuariogapd_norm]

    if telefone_norm:
        return "regexp_replace(COALESCE(telefone, ''), '\\D', '', 'g') = %s", [telefone_norm]

    return None, []


# ==========================================================
# LOCALIZAÇÃO DO CIDADÃO
# ==========================================================

def buscar_cidadao_por_identificadores(
    prontuariogapd: str | None,
    telefone: str | None
):
    """
    Localiza cidadãos distintos.

    Regras:
    - prontuário é identificador prioritário;
    - telefone só é usado quando não houver prontuário;
    - se houver telefone compartilhado, pode retornar múltiplos cidadãos;
    - deduplicação prioriza prontuariogapd e usa nome como fallback.
    """
    filtro_sql, params = _montar_filtro_identificacao_prioritario(
        prontuariogapd=prontuariogapd,
        telefone=telefone
    )

    if not filtro_sql:
        return []

    query = f"""
        SELECT
            id_notificacao,
            prontuariogapd,
            nome,
            telefone,
            datanotificacao
        FROM notificacao
        WHERE {filtro_sql}
        ORDER BY datanotificacao DESC NULLS LAST, id_notificacao DESC
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            registros = cur.fetchall()

            cidadaos_unicos = {}
            for r in registros:
                chave = normalizar_texto(r.get("prontuariogapd")) or normalizar_texto(r.get("nome"))
                if chave and chave not in cidadaos_unicos:
                    cidadaos_unicos[chave] = {
                        "prontuariogapd": normalizar_texto(r.get("prontuariogapd")),
                        "nome": normalizar_texto(r.get("nome")),
                        "telefone": normalizar_texto(r.get("telefone"))
                    }

            return list(cidadaos_unicos.values())
    finally:
        conn.close()


# ==========================================================
# REGISTRO ELEGÍVEL DO SERVIÇO SOLICITADO
# ==========================================================

def buscar_registro_servico_elegivel_para_continuidade(
    prontuariogapd: str | None,
    telefone: str | None,
    servicoespecializado: str | None
):
    """
    Busca o registro mais recente do serviço solicitado para o cidadão correto,
    já filtrando somente registros elegíveis para continuidade automática.

    Regras:
    - se houver prontuário, a busca usa somente prontuário;
    - telefone só é usado quando não houver prontuário;
    - o serviço deve coincidir exatamente;
    - nesta versão, somente statusagenda = AGENDADO é elegível.
    """
    servico_norm = normalizar_servico(servicoespecializado)
    if not servico_norm:
        return None

    filtro_sql, params = _montar_filtro_identificacao_prioritario(
        prontuariogapd=prontuariogapd,
        telefone=telefone
    )

    if not filtro_sql:
        return None

    query = f"""
        SELECT
            id_notificacao,
            prontuariogapd,
            nome,
            telefone,
            servicoespecializado,
            tipoagenda,
            situacaonotificacao,
            statusagenda,
            datanotificacao
        FROM notificacao
        WHERE UPPER(TRIM(servicoespecializado)) = %s
          AND UPPER(TRIM(COALESCE(statusagenda, ''))) = 'AGENDADO'
          AND {filtro_sql}
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


# ==========================================================
# ELEGIBILIDADE DE CONTINUIDADE
# ==========================================================

def statusagenda_elegivel_para_continuidade(statusagenda: str | None) -> bool:
    """
    Verifica se o statusagenda permite continuidade automática.

    Nesta versão:
    - somente statusagenda = AGENDADO é elegível.
    """
    status_norm = normalizar_texto(statusagenda)
    if not status_norm:
        return False
    return status_norm.upper() in STATUS_ELEGIVEIS_CONTINUIDADE