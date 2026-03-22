import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings


def buscar_cidadao_por_telefone(telefone: str):
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM public.agendamento
                WHERE telefone = %s
                ORDER BY id_agendamento DESC
                      """,
                (telefone,),
            )

            return cur.fetchone()
            
    finally:
        conn.close()


def buscar_cidadao_por_prontuario(prontuario: str):
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM public.agendamento
                WHERE prontuariogapd = %s
                ORDER BY id_agendamento DESC
                """,
                (prontuario,),
            )

            return cur.fetchall()
            
    finally:
        conn.close()