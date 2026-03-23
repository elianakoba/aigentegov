import re
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def normalizar_telefone(telefone: str | None) -> str | None:
    if not telefone:
        return None
    return re.sub(r"\D", "", telefone)


def converter_prontuario_para_string(registro: dict | None) -> dict | None:
    if not registro:
        return registro

    if registro.get("prontuariogapd") is not None:
        registro["prontuariogapd"] = str(registro["prontuariogapd"])

    if registro.get("horaagendamento") is not None:
        registro["horaagendamento"] = str(registro["horaagendamento"])

    return registro


def converter_lista_prontuario_para_string(registros: list[dict]) -> list[dict]:
    if not registros:
        return registros

    return [converter_prontuario_para_string(dict(item)) for item in registros]


# ==========================================================
# LOCALIZAÇÃO DO CIDADÃO
# ==========================================================

def buscar_cidadaos_por_telefone(telefone: str):
    """
    Localiza possíveis cidadãos a partir do telefone informado.
    O telefone serve apenas como etapa inicial de identificação.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    prontuariogapd,
                    nome
                FROM notificacao
                WHERE regexp_replace(COALESCE(telefone, ''), '[^0-9]', '', 'g') = %s
                  AND prontuariogapd IS NOT NULL
                ORDER BY nome, prontuariogapd
                """,
                (telefone,)
            )
            resultados = cur.fetchall()
            return converter_lista_prontuario_para_string(resultados)
    finally:
        conn.close()


def buscar_cidadao_por_prontuario(prontuariogapd: str):
    """
    Localiza um cidadão pelo prontuário.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    prontuariogapd,
                    nome
                FROM notificacao
                WHERE prontuariogapd = %s
                ORDER BY id_notificacao DESC
                LIMIT 1
                """,
                (prontuariogapd,)
            )
            resultado = cur.fetchone()
            return converter_prontuario_para_string(resultado)
    finally:
        conn.close()


# ==========================================================
# CONSULTA DE AGENDAMENTO
# ==========================================================

def buscar_agendamentos_por_prontuario(prontuariogapd: str):
    """
    Busca todos os agendamentos válidos do cidadão a partir da data atual.

    Observação:
    - esta consulta retorna todos os agendamentos registrados para o cidadão
      com dataagendamento >= CURRENT_DATE;
    - a ordenação garante que o primeiro item da lista seja o próximo agendamento.
    """
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id_notificacao,
                    prontuariogapd,
                    nome,
                    servicoespecializado,
                    dataagendamento,
                    horaagendamento,
                    situacaonotificacao,
                    status_agenda,
                    observacaonotificacao,
                    origem,
                    destino
                FROM notificacao
                WHERE prontuariogapd = %s
                  AND dataagendamento IS NOT NULL
                  AND dataagendamento >= CURRENT_DATE
                ORDER BY
                    dataagendamento ASC,
                    horaagendamento ASC NULLS LAST,
                    id_notificacao ASC
                """,
                (prontuariogapd,)
            )
            resultados = cur.fetchall()
            return converter_lista_prontuario_para_string(resultados)
    finally:
        conn.close()


# ==========================================================
# ORQUESTRAÇÃO PRINCIPAL
# ==========================================================

def consultar_agendamento(dados_entrada: dict):
    """
    Consulta os agendamentos de determinado cidadão.

    Regras:
    1. O telefone serve apenas para localizar possíveis prontuários.
    2. Quando houver mais de um cidadão para o mesmo telefone, a API retorna
       ESCOLHER_PRONTUARIO para que o agente peça qual cidadão deve ser consultado.
    3. A consulta final é feita por prontuariogapd.
    4. A resposta apresenta os agendamentos registrados do cidadão,
       podendo haver mais de um.
    5. São considerados apenas registros com dataagendamento >= CURRENT_DATE.
    """
    telefone = normalizar_telefone(dados_entrada.get("telefone"))
    prontuariogapd = dados_entrada.get("prontuariogapd")

    if prontuariogapd is not None:
        prontuariogapd = str(prontuariogapd).strip()

    if not telefone and not prontuariogapd:
        return {
            "sucesso": True,
            "proxima_acao": "INFORMAR_DADOS_OBRIGATORIOS",
            "mensagem": "É obrigatório informar telefone ou prontuariogapd.",
            "dados": {
                "quantidade_cidadaos_encontrados": 0,
                "cidadaos_localizados": [],
                "possui_agendamento": False,
                "quantidade_agendamentos_encontrados": 0,
                "proximo_agendamento": None,
                "agendamentos": [],
                "campos_pendentes": ["telefone_ou_prontuariogapd"]
            }
        }

    if prontuariogapd:
        cidadao = buscar_cidadao_por_prontuario(prontuariogapd)

        if not cidadao:
            return {
                "sucesso": True,
                "proxima_acao": "ENCAMINHAR_ATENDENTE_HUMANO",
                "mensagem": "Não foi possível localizar cidadão para o prontuário informado.",
                "dados": {
                    "quantidade_cidadaos_encontrados": 0,
                    "cidadaos_localizados": [],
                    "possui_agendamento": False,
                    "quantidade_agendamentos_encontrados": 0,
                    "proximo_agendamento": None,
                    "agendamentos": [],
                    "campos_pendentes": None
                }
            }

        agendamentos = buscar_agendamentos_por_prontuario(prontuariogapd)

        if not agendamentos:
            return {
                "sucesso": True,
                "proxima_acao": "INFORMAR_SEM_AGENDAMENTO",
                "mensagem": "Não foi localizado agendamento a partir da data atual para o prontuário informado.",
                "dados": {
                    "quantidade_cidadaos_encontrados": 1,
                    "cidadaos_localizados": [],
                    "possui_agendamento": False,
                    "quantidade_agendamentos_encontrados": 0,
                    "proximo_agendamento": None,
                    "agendamentos": [],
                    "campos_pendentes": None
                }
            }

        return {
            "sucesso": True,
            "proxima_acao": "EXIBIR_DADOS_AGENDAMENTO",
            "mensagem": "Foram localizados agendamentos para o cidadão informado.",
            "dados": {
                "quantidade_cidadaos_encontrados": 1,
                "cidadaos_localizados": [],
                "possui_agendamento": True,
                "quantidade_agendamentos_encontrados": len(agendamentos),
                "proximo_agendamento": agendamentos[0],
                "agendamentos": agendamentos,
                "campos_pendentes": None
            }
        }

    cidadaos = buscar_cidadaos_por_telefone(telefone)

    if not cidadaos:
        return {
            "sucesso": True,
            "proxima_acao": "ENCAMINHAR_ATENDENTE_HUMANO",
            "mensagem": "Não foi possível localizar cidadão para o telefone informado.",
            "dados": {
                "quantidade_cidadaos_encontrados": 0,
                "cidadaos_localizados": [],
                "possui_agendamento": False,
                "quantidade_agendamentos_encontrados": 0,
                "proximo_agendamento": None,
                "agendamentos": [],
                "campos_pendentes": None
            }
        }

    if len(cidadaos) > 1:
        return {
            "sucesso": True,
            "proxima_acao": "ESCOLHER_PRONTUARIO",
            "mensagem": (
                "Foi localizado mais de um cidadão para o telefone informado. "
                "Solicite ao usuário qual prontuário deve ser consultado."
            ),
            "dados": {
                "quantidade_cidadaos_encontrados": len(cidadaos),
                "cidadaos_localizados": cidadaos,
                "possui_agendamento": False,
                "quantidade_agendamentos_encontrados": 0,
                "proximo_agendamento": None,
                "agendamentos": [],
                "campos_pendentes": None
            }
        }

    prontuariogapd_unico = str(cidadaos[0]["prontuariogapd"])
    agendamentos = buscar_agendamentos_por_prontuario(prontuariogapd_unico)

    if not agendamentos:
        return {
            "sucesso": True,
            "proxima_acao": "INFORMAR_SEM_AGENDAMENTO",
            "mensagem": "Não foi localizado agendamento a partir da data atual para o prontuário informado.",
            "dados": {
                "quantidade_cidadaos_encontrados": 1,
                "cidadaos_localizados": [],
                "possui_agendamento": False,
                "quantidade_agendamentos_encontrados": 0,
                "proximo_agendamento": None,
                "agendamentos": [],
                "campos_pendentes": None
            }
        }

    return {
        "sucesso": True,
        "proxima_acao": "EXIBIR_DADOS_AGENDAMENTO",
        "mensagem": "Foram localizados agendamentos para o cidadão informado.",
        "dados": {
            "quantidade_cidadaos_encontrados": 1,
            "cidadaos_localizados": [],
            "possui_agendamento": True,
            "quantidade_agendamentos_encontrados": len(agendamentos),
            "proximo_agendamento": agendamentos[0],
            "agendamentos": agendamentos,
            "campos_pendentes": None
        }
    }