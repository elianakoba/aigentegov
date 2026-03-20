from fastapi import APIRouter, Depends, Body

from app.core.security import validar_api_key
from app.schemas.localiza_cidadao_para_agendamento import (
    LocalizaCidadaoParaAgendamentoRequest,
    LocalizaCidadaoParaAgendamentoResponse,
    DadosRetornoLocalizaCidadaoParaAgendamentoResponse
)
from app.db.localiza_cidadao_para_agendamento import (
    buscar_cidadao_por_identificadores,
    buscar_servicos_ja_utilizados_cidadao,
    buscar_notificacao_base_servico
)


router = APIRouter(
    prefix="/v1/localiza-cidadao-para-agendamento",
    tags=["Localização do cidadão para agendamento"],
    dependencies=[Depends(validar_api_key)]
)


def normalizar_servico(valor: str | None) -> str | None:
    if not valor:
        return None
    return valor.strip().upper()


def normalizar_texto(valor):
    if valor is None:
        return None
    return str(valor).strip()


@router.post(
    "",
    response_model=LocalizaCidadaoParaAgendamentoResponse,
    summary="Localizar cidadão e validar se pode prosseguir para o agendamento",
    description=(
        "Etapa anterior ao agendamento. "
        "Esta rota localiza o cidadão por prontuário GAPD ou telefone, "
        "verifica se o serviço solicitado já foi utilizado anteriormente e, "
        "quando elegível, devolve o id_notificacao_base que deverá ser usado "
        "na API principal de agendamento."
        "\n\n"
        "Regras esperadas pelo agente:"
        "\n"
        "1. Sempre chamar esta rota antes da API de agendamento."
        "\n"
        "2. Se a resposta retornar PROSSEGUIR_AGENDAMENTO, usar o id_notificacao_base retornado na próxima chamada."
        "\n"
        "3. Se a resposta retornar INFORMAR_DADOS_OBRIGATORIOS, solicitar os dados faltantes ao cidadão."
        "\n"
        "4. Se a resposta retornar ENCAMINHAR_ATENDENTE_HUMANO, não tentar autoagendamento."
    )
)
def localiza_cidadao_para_agendamento(
    payload: LocalizaCidadaoParaAgendamentoRequest = Body(
        ...,
        openapi_examples={
            "busca_por_prontuario": {
                "summary": "Busca por prontuário GAPD",
                "description": "Use quando o prontuário do cidadão estiver disponível.",
                "value": {
                    "prontuariogapd": "123456",
                    "servicoespecializado": "FISIOTERAPIA",
                    "canal_origem": "whatsapp"
                }
            },
            "busca_por_telefone": {
                "summary": "Busca por telefone",
                "description": "Use quando a identificação ocorrer pelo telefone ou WhatsApp do cidadão.",
                "value": {
                    "telefone": "(11) 99999-8888",
                    "servicoespecializado": "TRANSPORTE",
                    "canal_origem": "web"
                }
            }
        }
    )
):
    # ======================================================
    # 1) VALIDA CAMPOS MÍNIMOS
    # ======================================================
    campos_pendentes = []

    if not payload.prontuariogapd and not payload.telefone:
        campos_pendentes.append("prontuariogapd_ou_telefone")

    if not payload.servicoespecializado:
        campos_pendentes.append("servicoespecializado")

    if campos_pendentes:
        return LocalizaCidadaoParaAgendamentoResponse(
            sucesso=False,
            proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
            mensagem="Faltam dados obrigatórios para localizar o cidadão e validar o serviço.",
            dados=DadosRetornoLocalizaCidadaoParaAgendamentoResponse(
                campos_pendentes=campos_pendentes
            )
        )

    # Normalização defensiva
    prontuariogapd = normalizar_texto(payload.prontuariogapd)
    telefone = normalizar_texto(payload.telefone)
    servicoespecializado = normalizar_texto(payload.servicoespecializado)

    # ======================================================
    # 2) LOCALIZA O CIDADÃO
    # ======================================================
    cidadao = buscar_cidadao_por_identificadores(
        prontuariogapd=prontuariogapd,
        telefone=telefone
    )

    if not cidadao:
        return LocalizaCidadaoParaAgendamentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "Não foi localizado cadastro válido do cidadão para iniciar o autoatendimento. "
                "O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoLocalizaCidadaoParaAgendamentoResponse(
                cidadao_identificado=False,
                servico_elegivel_autoagendamento=False,
                servicoespecializado=servicoespecializado
            )
        )

    prontuariogapd_retorno = normalizar_texto(cidadao.get("prontuariogapd"))
    telefone_retorno = normalizar_texto(cidadao.get("telefone"))
    nome_retorno = normalizar_texto(cidadao.get("nome"))

    # ======================================================
    # 3) BUSCA O HISTÓRICO DE SERVIÇOS
    # ======================================================
    servicos_ja_utilizados = buscar_servicos_ja_utilizados_cidadao(
        prontuariogapd=prontuariogapd or prontuariogapd_retorno,
        telefone=telefone or telefone_retorno
    )

    servico_solicitado_norm = normalizar_servico(servicoespecializado)
    servicos_historico_norm = {
        normalizar_servico(s) for s in servicos_ja_utilizados if s
    }

    servico_elegivel = servico_solicitado_norm in servicos_historico_norm

    if not servico_elegivel:
        return LocalizaCidadaoParaAgendamentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O cidadão foi identificado, porém o serviço solicitado não possui histórico anterior "
                "de utilização. O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoLocalizaCidadaoParaAgendamentoResponse(
                cidadao_identificado=True,
                servico_elegivel_autoagendamento=False,
                prontuariogapd=prontuariogapd_retorno,
                nome=nome_retorno,
                telefone=telefone_retorno,
                servicoespecializado=servicoespecializado,
                servicos_ja_utilizados=servicos_ja_utilizados
            )
        )

    # ======================================================
    # 4) BUSCA A NOTIFICAÇÃO-BASE DO MESMO SERVIÇO
    # ======================================================
    notificacao_base = buscar_notificacao_base_servico(
        prontuariogapd=prontuariogapd or prontuariogapd_retorno,
        telefone=telefone or telefone_retorno,
        servicoespecializado=servicoespecializado
    )

    if not notificacao_base:
        return LocalizaCidadaoParaAgendamentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O cidadão foi identificado e possui histórico do serviço, "
                "mas não foi localizada uma notificação-base válida para iniciar o autoagendamento. "
                "O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoLocalizaCidadaoParaAgendamentoResponse(
                cidadao_identificado=True,
                servico_elegivel_autoagendamento=False,
                prontuariogapd=prontuariogapd_retorno,
                nome=nome_retorno,
                telefone=telefone_retorno,
                servicoespecializado=servicoespecializado,
                servicos_ja_utilizados=servicos_ja_utilizados
            )
        )

    # ======================================================
    # 5) LIBERA O FLUXO DE AGENDAMENTO
    # ======================================================
    return LocalizaCidadaoParaAgendamentoResponse(
        sucesso=True,
        proxima_acao="PROSSEGUIR_AGENDAMENTO",
        mensagem="Cidadão localizado e serviço elegível para continuidade do autoagendamento.",
        dados=DadosRetornoLocalizaCidadaoParaAgendamentoResponse(
            cidadao_identificado=True,
            servico_elegivel_autoagendamento=True,
            id_notificacao_base=notificacao_base["id_notificacao"],
            prontuariogapd=normalizar_texto(notificacao_base.get("prontuariogapd")),
            nome=normalizar_texto(notificacao_base.get("nome")),
            telefone=normalizar_texto(notificacao_base.get("telefone")),
            servicoespecializado=servicoespecializado,
            tipoagenda=normalizar_texto(notificacao_base.get("tipoagenda")),
            servicos_ja_utilizados=servicos_ja_utilizados
        )
    )