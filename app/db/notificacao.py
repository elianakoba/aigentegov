import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


def listar_notificacoes():
    """
    Retorna todas as notificações cadastradas.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_notificacao,
                    dataagendamento,
                    horaagendamento,
                    prontuariogapd,
                    nome,
                    telefone,
                    servicoespecializado,
                    origem,
                    destino,
                    situacaonotificacao,
                    datanotificacao,
                    observacaonotificacao,
                    situacaoresposta,
                    dataresposta,
                    observacaoresposta
                FROM notificacao
                Where (situacaonotificacao is null) OR
	            (situacaonotificacao = 'NOTIFICADO' AND situacaoresposta IS NULL)          
                ORDER BY id_notificacao DESC
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def buscar_notificacao_por_id(id_notificacao: int):
    """
    Retorna uma única notificação pelo ID.
    Usado para confirmação de horário.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_notificacao,
                    dataagendamento,
                    horaagendamento,
                    prontuariogapd,
                    nome,
                    telefone,
                    servicoespecializado,
                    origem,
                    destino,
                    situacaonotificacao,
                    datanotificacao,
                    observacaonotificacao,
                    situacaoresposta,
                    dataresposta,
                    observacaoresposta
                FROM notificacao
                WHERE id_notificacao = %s
                """,
                (id_notificacao,)
            )
            return cur.fetchone()
    finally:
        conn.close()
