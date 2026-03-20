import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

# Busca na  a tabela notificacao, pois está sendo considerado como repositóro dos agendamentos oficiais 
# Tabela agendamento apenas para historico de solicitações de agendamento
def buscar_agendamento_por_prontuario(prontuariogapd: int): 
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM notificacao
                WHERE prontuariogapd = %s
                AND dataagendamento >= CURRENT_DATE;
                """,
                (prontuariogapd,),
            )
            return cur.fetchall()
    finally:
        conn.close()

def buscar_agendamento_por_id(id_agendamentido: int):
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM notificacao
                WHERE id_notificacao = %s
                """,
                (id_notificacao,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def inserir_agendamento_variavel(dados: dict):
    """
    Insere um agendamento do tipo VARIAVEL.
    Retorna o registro inserido.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO agendamento
                (
                    tipo_agendamento, status, motivo_status, status_atualizado_em,
                    data_preferencia_inicio, data_preferencia_fim, diasemana, periodo_preferencial,
                    prontuariogapd, nome, telefone, cpf,
                    servico_id, servicoespecializado, permite_agente_ia,
                    canal, solicitado_por, conversa_id, mensagem_id, data_agendamento,
                    origem, destino,
                    observacao, ativo
                )
                VALUES
                (
                    %(tipo_agendamento)s, %(status)s, %(motivo_status)s, %(status_atualizado_em)s,
                    %(data_preferencia_inicio)s, %(data_preferencia_fim)s, %(diasemana)s, %(periodo_preferencial)s,
                    %(prontuariogapd)s, %(nome)s, %(telefone)s, %(cpf)s,
                    %(servico_id)s, %(servicoespecializado)s, %(permite_agente_ia)s,
                    %(canal)s, %(solicitado_por)s, %(conversa_id)s, %(mensagem_id)s, %(data_agendamento)s, 
                    %(origem)s, %(destino)s,
                    %(observacao)s, %(ativo)s
                )
                RETURNING *
                """,
                dados,
            )
            row = cur.fetchone()
            conn.commit()
            return row
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def atualizar_status_agendamento(id_agendamento: int, status: str, motivo_status: str | None = None):
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE agendamento
                SET
                    status = %s,
                    motivo_status = %s,
                    status_atualizado_em = now(),
                    atualizado_em = now()
                WHERE id_agendamento = %s
                RETURNING *
                """,
                (status, motivo_status, id_agendamento),
            )
            row = cur.fetchone()
            conn.commit()
            return row
    except:
        conn.rollback()
        raise
    finally:
        conn.close()