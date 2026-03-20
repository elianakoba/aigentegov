import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


def atualizar_status_notificacao(
    id_notificacao: int,
    situacaonotificacao: str | None,
    observacaonotificacao: str | None,
    situacaoresposta: str | None,
    observacaoresposta: str | None,
):
    """
    Atualiza status de notificação SEM sobrescrever eventos anteriores.

    - Se o campo não vier no request -> mantém o valor atual (COALESCE).
    - Datas:
        * datanotificacao só é gravada quando situacaonotificacao vier e datanotificacao estiver NULL
        * dataresposta só é gravada quando situacaoresposta vier e dataresposta estiver NULL
    """

    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE public.notificacao
                SET
                    situacaonotificacao = COALESCE(%s, situacaonotificacao),
                    observacaonotificacao = COALESCE(%s, observacaonotificacao),
                    datanotificacao = CASE
                        WHEN %s IS NOT NULL AND datanotificacao IS NULL
                        THEN CURRENT_TIMESTAMP
                        ELSE datanotificacao
                    END,

                    situacaoresposta = COALESCE(%s, situacaoresposta),
                    observacaoresposta = COALESCE(%s, observacaoresposta),
                    dataresposta = CASE
                        WHEN %s IS NOT NULL AND dataresposta IS NULL
                        THEN CURRENT_TIMESTAMP
                        ELSE dataresposta
                    END
                WHERE id_notificacao = %s
                RETURNING
                    id_notificacao,
                    situacaonotificacao,
                    datanotificacao,
                    situacaoresposta,
                    dataresposta
                """,
                (
                    situacaonotificacao,
                    observacaonotificacao,
                    situacaonotificacao,
                    situacaoresposta,
                    observacaoresposta,
                    situacaoresposta,
                    id_notificacao,
                ),
            )

            row = cur.fetchone()
            conn.commit()
            return row
    finally:
        conn.close()
