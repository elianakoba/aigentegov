import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


# ==========================================================
# BUSCA DA NOTIFICAÇÃO BASE
# ==========================================================

def buscar_notificacao_por_id(id_notificacao: int):
    """
    Busca a notificação base usada para obter os dados do cidadão
    e demais informações de contexto disponíveis nesta POC.
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
                    observacaoresposta,
                    tipoagenda,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                FROM notificacao
                WHERE id_notificacao = %s
                """,
                (id_notificacao,)
            )
            return cur.fetchone()
    finally:
        conn.close()


# ==========================================================
# CONSULTA DE DISPONIBILIDADE PARA SLOT FIXO
# ==========================================================

def buscar_slots_disponiveis(
    servicoespecializado: str,
    dataagendamento,
    horaagendamento: str | None = None
):
    """
    Busca slots disponíveis para o serviço e data informados.
    Se horaagendamento for informada, tenta o horário exato.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_slot,
                    servicoespecializado,
                    dataagenda,
                    horaagenda,
                    unidade,
                    situacao
                FROM agenda_slot_fixo
                WHERE servicoespecializado = %s
                  AND dataagenda = %s
                  AND (%s IS NULL OR horaagenda = %s)
                  AND situacao = 'DISPONIVEL'
                ORDER BY horaagenda
                """,
                (servicoespecializado, dataagendamento, horaagendamento, horaagendamento)
            )
            return cur.fetchall()
    finally:
        conn.close()


def buscar_slots_alternativos(
    servicoespecializado: str,
    dataagendamento,
    horaagendamento: str | None = None,
    limite: int = 5
):
    """
    Busca alternativas quando não houver vaga exata.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_slot,
                    servicoespecializado,
                    dataagenda,
                    horaagenda,
                    unidade,
                    situacao
                FROM agenda_slot_fixo
                WHERE servicoespecializado = %s
                  AND dataagenda >= %s
                  AND situacao = 'DISPONIVEL'
                  AND NOT (
                        dataagenda = %s
                    AND (%s IS NULL OR horaagenda = %s)
                  )
                ORDER BY dataagenda, horaagenda
                LIMIT %s
                """,
                (
                    servicoespecializado,
                    dataagendamento,
                    dataagendamento,
                    horaagendamento,
                    horaagendamento,
                    limite
                )
            )
            return cur.fetchall()
    finally:
        conn.close()


# ==========================================================
# INSERÇÃO DE NOVO REGISTRO EM NOTIFICACAO
# ==========================================================

def inserir_notificacao_agendamento(
    notificacao_base: dict,
    servicoespecializado: str,
    tipoagenda: str,
    origem: str | None,
    destino: str | None,
    dataagendamento,
    horaagendamento: str | None,
    situacaonotificacao: str,
    observacaonotificacao: str | None,
    statusagenda: str | None,
    datapreferencia=None,
    horapreferencia: str | None = None,
    datasolicitacao=None,
    dataautorizacao=None
):
    """
    Insere um novo registro em notificacao copiando os dados do cidadão
    da notificação base e gravando os dados da nova solicitação/agendamento.

    Regras:
    - datapreferencia/horapreferencia representam a intenção do cidadão.
    - dataagendamento/horaagendamento representam confirmação efetiva.
    - quando houver apenas solicitação, dataagendamento/horaagendamento devem permanecer nulos.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO notificacao (
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
                    observacaoresposta,
                    tipoagenda,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    %s,
                    NULL,
                    NULL,
                    NULL,
                    %s,
                    %s,
                    %s,
                    %s,
                    COALESCE(%s, NOW()),
                    %s
                )
                RETURNING
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
                    observacaonotificacao,
                    tipoagenda,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                """,
                (
                    dataagendamento,
                    horaagendamento,
                    notificacao_base.get("prontuariogapd"),
                    notificacao_base.get("nome"),
                    notificacao_base.get("telefone"),
                    servicoespecializado,
                    origem,
                    destino,
                    situacaonotificacao,
                    observacaonotificacao,
                    tipoagenda,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                )
            )
            registro = cur.fetchone()
        conn.commit()
        return registro
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==========================================================
# CONCLUSÃO DE AGENDAMENTO SLOT FIXO
# ==========================================================

def registrar_agendamento_slot_fixo(
    notificacao_base: dict,
    id_slot: int,
    servicoespecializado: str,
    tipoagenda: str,
    origem: str | None,
    destino: str | None,
    observacaonotificacao: str | None,
    datapreferencia=None,
    horapreferencia: str | None = None,
    datasolicitacao=None,
    dataautorizacao=None
):
    """
    Efetiva o agendamento de um serviço do tipo slot_fixo.

    Fluxo:
    1. valida o slot;
    2. insere um novo registro em notificacao;
    3. vincula o slot à nova notificação;
    4. muda a situação do slot para RESERVADO.

    Aqui, diferentemente da mera solicitação, dataagendamento e horaagendamento
    são preenchidos com os valores efetivamente confirmados no slot.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_slot,
                    servicoespecializado,
                    dataagenda,
                    horaagenda,
                    unidade,
                    situacao,
                    id_notificacao
                FROM agenda_slot_fixo
                WHERE id_slot = %s
                FOR UPDATE
                """,
                (id_slot,)
            )
            slot = cur.fetchone()

            if not slot:
                raise ValueError("Slot não encontrado.")

            if slot["situacao"] != "DISPONIVEL":
                raise ValueError("O slot informado não está disponível.")

            if slot["servicoespecializado"] != servicoespecializado:
                raise ValueError("O slot informado não pertence ao serviço solicitado.")

            cur.execute(
                """
                INSERT INTO notificacao (
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
                    observacaoresposta,
                    tipoagenda,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'AGENDADO',
                    NOW(),
                    %s,
                    NULL,
                    NULL,
                    NULL,
                    %s,
                    'AGENDADO',
                    %s,
                    %s,
                    COALESCE(%s, NOW()),
                    %s
                )
                RETURNING
                    id_notificacao,
                    dataagendamento,
                    horaagendamento,
                    situacaonotificacao,
                    tipoagenda,
                    servicoespecializado,
                    origem,
                    destino,
                    statusagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                """,
                (
                    slot["dataagenda"],
                    slot["horaagenda"],
                    notificacao_base.get("prontuariogapd"),
                    notificacao_base.get("nome"),
                    notificacao_base.get("telefone"),
                    servicoespecializado,
                    origem,
                    destino,
                    observacaonotificacao,
                    tipoagenda,
                    datapreferencia,
                    horapreferencia,
                    datasolicitacao,
                    dataautorizacao
                )
            )
            nova_notificacao = cur.fetchone()

            cur.execute(
                """
                UPDATE agenda_slot_fixo
                SET
                    situacao = 'RESERVADO',
                    id_notificacao = %s,
                    dataatualizacao = NOW()
                WHERE id_slot = %s
                """,
                (nova_notificacao["id_notificacao"], id_slot)
            )

        conn.commit()

        return {
            "notificacao": nova_notificacao,
            "slot": slot
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()