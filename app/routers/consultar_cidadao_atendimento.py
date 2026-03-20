from fastapi import APIRouter, Depends, Body

from app.core.security import validar_api_key
from app.schemas.consultar_cidadao_atendimento import (
    ConsultarCidadaoAtendimentoRequest,
    ConsultarCidadaoAtendimentoResponse,
    DadosRetornoConsultarCidadaoAtendimentoResponse
)
from app.db.consultar_cidadao_atendimento import (
    buscar_cidadao_por_identificadores,
    buscar_servicos_ja_utilizados_cidadao,
    buscar_notificacao_base_servico,
    buscar_ultimo_registro_relevante_cidadao
)


router = APIRouter(
    prefix="/v1/consultar-cidadao-atendimento",
    tags=["Consulta do cidadão para atendimento"],
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
    response_model=ConsultarCidadaoAtendimentoResponse,
    summary="Consultar cidadão para atendimento",
    description=(
        "API responsável por localizar o cidadão por prontuário GAPD ou telefone "
        "e retornar informações para apoio ao atendimento. "
        "O comportamento da consulta é direcionado pela intenção informada no payload."
        "\n\n"
        "Intenções atualmente suportadas:"
        "\n"
        "1. CONSULTAR_DADOS_CIDADAO"
        "\n"
        "2. VALIDAR_CONTINUIDADE_ATENDIMENTO"
    )
)
def consultar_cidadao_atendimento(
    payload: ConsultarCidadaoAtendimentoRequest = Body(
        ...,
        openapi_examples={
            "consultar_dados_cidadao": {
                "summary": "Consultar dados do cidadão",
                "description": "Use quando o objetivo for localizar o cidadão e obter seus dados básicos para apoio ao atendimento.",
                "value": {
                    "telefone": "(11) 99999-8888",
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "whatsapp"
                }
            },
            "validar_continuidade_atendimento": {
                "summary": "Validar continuidade do atendimento",
                "description": "Use quando o objetivo for verificar se há continuidade possível para um determinado serviço.",
                "value": {
                    "prontuariogapd": "123456",
                    "servicoespecializado": "FISIOTERAPIA",
                    "intencao": "VALIDAR_CONTINUIDADE_ATENDIMENTO",
                    "canal_origem": "whatsapp"
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

    if payload.intencao == "VALIDAR_CONTINUIDADE_ATENDIMENTO" and not payload.servicoespecializado:
        campos_pendentes.append("servicoespecializado")

    if campos_pendentes:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
            mensagem="Faltam dados obrigatórios para executar a consulta do cidadão para atendimento.",
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                intencao=payload.intencao,
                servicoespecializado=payload.servicoespecializado,
                campos_pendentes=campos_pendentes
            )
        )

    # ======================================================
    # 2) NORMALIZAÇÃO DEFENSIVA
    # ======================================================
    prontuariogapd = normalizar_texto(payload.prontuariogapd)
    telefone = normalizar_texto(payload.telefone)
    servicoespecializado = normalizar_texto(payload.servicoespecializado)

    # ======================================================
    # 3) LOCALIZA O CIDADÃO
    # ======================================================
    cidadao = buscar_cidadao_por_identificadores(
        prontuariogapd=prontuariogapd,
        telefone=telefone
    )

    if not cidadao:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "Não foi localizado cadastro válido do cidadão para continuidade do atendimento. "
                "O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=False,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado
            )
        )

    prontuariogapd_retorno = normalizar_texto(cidadao.get("prontuariogapd"))
    telefone_retorno = normalizar_texto(cidadao.get("telefone"))
    nome_retorno = normalizar_texto(cidadao.get("nome"))

    # ======================================================
    # 4) INTENÇÃO: CONSULTAR_DADOS_CIDADAO
    # ======================================================
    if payload.intencao == "CONSULTAR_DADOS_CIDADAO":
        servicos_ja_utilizados = buscar_servicos_ja_utilizados_cidadao(
            prontuariogapd=prontuariogapd or prontuariogapd_retorno,
            telefone=telefone or telefone_retorno
        )

        ultimo_registro = buscar_ultimo_registro_relevante_cidadao(
            prontuariogapd=prontuariogapd or prontuariogapd_retorno,
            telefone=telefone or telefone_retorno
        )

        return ConsultarCidadaoAtendimentoResponse(
            sucesso=True,
            proxima_acao="EXIBIR_DADOS_CIDADAO",
            mensagem="Cidadão localizado com sucesso.",
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_retorno,
                nome=nome_retorno,
                telefone=telefone_retorno,
                intencao=payload.intencao,
                servicos_ja_utilizados=servicos_ja_utilizados,
                ultimo_servicoespecializado=normalizar_texto(ultimo_registro.get("servicoespecializado")) if ultimo_registro else None,
                ultima_situacaonotificacao=normalizar_texto(ultimo_registro.get("situacaonotificacao")) if ultimo_registro else None,
                ultimo_statusagenda=normalizar_texto(ultimo_registro.get("statusagenda")) if ultimo_registro else None,
                continuidade_atendimento=True
            )
        )

    # ======================================================
    # 5) INTENÇÃO: VALIDAR_CONTINUIDADE_ATENDIMENTO
    # ======================================================
    servicos_ja_utilizados = buscar_servicos_ja_utilizados_cidadao(
        prontuariogapd=prontuariogapd or prontuariogapd_retorno,
        telefone=telefone or telefone_retorno
    )

    servico_solicitado_norm = normalizar_servico(servicoespecializado)
    servicos_historico_norm = {
        normalizar_servico(s) for s in servicos_ja_utilizados if s
    }

    continuidade_atendimento = servico_solicitado_norm in servicos_historico_norm

    if not continuidade_atendimento:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O cidadão foi identificado, porém não há continuidade automática disponível "
                "para o serviço informado. O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_retorno,
                nome=nome_retorno,
                telefone=telefone_retorno,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado,
                servicos_ja_utilizados=servicos_ja_utilizados,
                continuidade_atendimento=False
            )
        )

    notificacao_base = buscar_notificacao_base_servico(
        prontuariogapd=prontuariogapd or prontuariogapd_retorno,
        telefone=telefone or telefone_retorno,
        servicoespecializado=servicoespecializado
    )

    if not notificacao_base:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O cidadão foi identificado e possui histórico do serviço, "
                "mas não foi localizado um registro-base válido para continuidade do atendimento. "
                "O caso deve ser encaminhado ao atendente humano."
            ),
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_retorno,
                nome=nome_retorno,
                telefone=telefone_retorno,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado,
                servicos_ja_utilizados=servicos_ja_utilizados,
                continuidade_atendimento=False
            )
        )

    return ConsultarCidadaoAtendimentoResponse(
        sucesso=True,
        proxima_acao="PROSSEGUIR_ATENDIMENTO",
        mensagem="Cidadão localizado e continuidade de atendimento validada com sucesso.",
        dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
            cidadao_identificado=True,
            prontuariogapd=normalizar_texto(notificacao_base.get("prontuariogapd")),
            nome=normalizar_texto(notificacao_base.get("nome")),
            telefone=normalizar_texto(notificacao_base.get("telefone")),
            intencao=payload.intencao,
            servicoespecializado=servicoespecializado,
            servicos_ja_utilizados=servicos_ja_utilizados,
            continuidade_atendimento=True,
            id_notificacao_base=notificacao_base["id_notificacao"],
            tipoagenda=normalizar_texto(notificacao_base.get("tipoagenda"))
        )
    )