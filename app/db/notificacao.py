import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


def obter_dia_semana_portugues(data_agendamento):
    if not data_agendamento:
        return None

    dias_semana = {
        0: "segunda-feira",
        1: "terça-feira",
        2: "quarta-feira",
        3: "quinta-feira",
        4: "sexta-feira",
        5: "sábado",
        6: "domingo"
    }
    return dias_semana.get(data_agendamento.weekday())


def listar_notificacoes():
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
                WHERE (situacaonotificacao IS NULL)
                   OR (situacaonotificacao = 'NOTIFICADO' AND situacaoresposta IS NULL)
                ORDER BY id_notificacao DESC
                """
            )
            resultados = cur.fetchall()

            for item in resultados:
                item["diadasemanaagendamento"] = obter_dia_semana_portugues(
                    item.get("dataagendamento")
                )

            return resultados
    finally:
        conn.close()


def buscar_notificacao_por_id(id_notificacao: int):
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
            resultado = cur.fetchone()

            if resultado:
                resultado["diadasemanaagendamento"] = obter_dia_semana_portugues(
                    resultado.get("dataagendamento")
                )

            return resultado
    finally:
        conn.close()