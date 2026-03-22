from fastapi import APIRouter, Depends, Body

from app.core.security import validar_api_key
from app.schemas.consultar_cidadao_atendimento import (
    ConsultarCidadaoAtendimentoRequest,
    ConsultarCidadaoAtendimentoResponse,
    DadosRetornoConsultarCidadaoAtendimentoResponse,
    CidadaoEncontradoOption
)
from app.db.consultar_cidadao_atendimento import (
    buscar_cidadao_por_identificadores,
    buscar_registro_servico_elegivel_para_continuidade,
    statusagenda_elegivel_para_continuidade
)


router = APIRouter(
    prefix="/v1/consultar-cidadao-atendimento",
    tags=["Consulta do cidadão para atendimento"],
    dependencies=[Depends(validar_api_key)]
)


def normalizar_texto(valor):
    if valor is None:
        return None
    return str(valor).strip()


@router.post(
    "",
    response_model=ConsultarCidadaoAtendimentoResponse,
    response_model_exclude_none=True,
    summary="Consultar cidadão para atendimento",
    description=(
        "API responsável por localizar o cidadão por prontuário GAPD ou telefone "
        "e retornar somente as informações pertinentes ao cenário solicitado.\n\n"

        "Campos obrigatórios gerais:\n"
        "- informar pelo menos um identificador: prontuariogapd ou telefone;\n"
        "- informar a intencao da consulta.\n\n"

        "Intenções suportadas:\n\n"

        "1. CONSULTAR_DADOS_CIDADAO\n"
        "   - Objetivo: localizar o cidadão e retornar apenas sua identificação básica.\n"
        "   - Campos obrigatórios: intencao + (prontuariogapd ou telefone).\n"
        "   - Campo servicoespecializado: não obrigatório.\n\n"

        "2. VALIDAR_CONTINUIDADE_ATENDIMENTO\n"
        "   - Objetivo: verificar se existe registro anterior do serviço solicitado "
        "para o cidadão correto e se o statusagenda desse registro permite continuidade automática.\n"
        "   - Campos obrigatórios: intencao + (prontuariogapd ou telefone) + servicoespecializado.\n\n"

        "Regras de identificação:\n"
        "- o prontuariogapd é o identificador prioritário quando disponível;\n"
        "- se a busca for feita apenas por telefone e houver mais de um cidadão vinculado ao número, "
        "a API retorna SELECIONAR_CIDADAO e apresenta a lista de pessoas encontradas;\n"
        "- nesse cenário, o agente deve solicitar ao usuário a escolha da pessoa correta antes de prosseguir.\n\n"

        "Regra de continuidade:\n"
        "- a continuidade automática só é permitida quando existir registro anterior do serviço solicitado "
        "para o cidadão correto e o statusagenda for elegível;\n"
        "- nesta versão, apenas statusagenda = AGENDADO é considerado elegível para prosseguir.\n\n"

        "Interpretação do campo proxima_acao:\n"
        "- EXIBIR_DADOS_CIDADAO: cidadão localizado e dados básicos disponíveis para consulta.\n"
        "- PROSSEGUIR_ATENDIMENTO: continuidade de atendimento validada com sucesso.\n"
        "- INFORMAR_DADOS_OBRIGATORIOS: faltam campos para processar a intenção informada.\n"
        "- ENCAMINHAR_ATENDENTE_HUMANO: não foi possível automatizar o atendimento.\n"
        "- SELECIONAR_CIDADAO: foi encontrado mais de um cidadão vinculado ao telefone informado."
    ),
    responses={
        200: {
            "description": "Resposta funcional da consulta do cidadão para atendimento."
        },
        401: {
            "description": "API key ausente ou inválida."
        },
        422: {
            "description": "Payload inválido."
        }
    }
)
def consultar_cidadao_atendimento(
    payload: ConsultarCidadaoAtendimentoRequest = Body(
        ...,
        openapi_examples={
            "consultar_dados_por_telefone": {
                "summary": "Consultar dados do cidadão por telefone",
                "description": (
                    "Use quando o objetivo for localizar o cidadão por telefone "
                    "e obter somente sua identificação básica."
                ),
                "value": {
                    "telefone": "(11) 99999-8888",
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "whatsapp"
                }
            },
            "consultar_dados_por_prontuario": {
                "summary": "Consultar dados do cidadão por prontuário",
                "description": (
                    "Use quando o prontuário GAPD estiver disponível e o objetivo for "
                    "consultar apenas a identificação do cidadão."
                ),
                "value": {
                    "prontuariogapd": "123456",
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "atendente"
                }
            },
            "validar_continuidade_sucesso": {
                "summary": "Validar continuidade do atendimento",
                "description": (
                    "Use quando for necessário verificar se existe registro anterior do "
                    "serviço solicitado e se o statusagenda permite continuidade automática."
                ),
                "value": {
                    "prontuariogapd": "123456",
                    "servicoespecializado": "FISIOTERAPIA",
                    "intencao": "VALIDAR_CONTINUIDADE_ATENDIMENTO",
                    "canal_origem": "whatsapp"
                }
            },
            "validar_continuidade_sem_servico": {
                "summary": "Exemplo inválido: falta servicoespecializado",
                "description": (
                    "Quando a intencao for VALIDAR_CONTINUIDADE_ATENDIMENTO, "
                    "o campo servicoespecializado deve ser enviado."
                ),
                "value": {
                    "telefone": "(11) 99999-8888",
                    "intencao": "VALIDAR_CONTINUIDADE_ATENDIMENTO",
                    "canal_origem": "whatsapp"
                }
            },
            "consulta_sem_identificador": {
                "summary": "Exemplo inválido: falta identificador",
                "description": (
                    "É obrigatório informar pelo menos um identificador: "
                    "prontuariogapd ou telefone."
                ),
                "value": {
                    "intencao": "CONSULTAR_DADOS_CIDADAO",
                    "canal_origem": "web"
                }
            }
        }
    )
):
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

    prontuariogapd = normalizar_texto(payload.prontuariogapd)
    telefone = normalizar_texto(payload.telefone)
    servicoespecializado = normalizar_texto(payload.servicoespecializado)

    lista_cidadaos = buscar_cidadao_por_identificadores(
        prontuariogapd=prontuariogapd,
        telefone=telefone
    )

    if not lista_cidadaos:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem="Não foi localizado cadastro válido do cidadão.",
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=False,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado
            )
        )

    if not prontuariogapd and len(lista_cidadaos) > 1:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=True,
            proxima_acao="SELECIONAR_CIDADAO",
            mensagem="Mais de um cidadão encontrado para este telefone. Selecione para continuar.",
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=False,
                multiplicidade_cidadaos=True,
                quantidade_cidadaos_encontrados=len(lista_cidadaos),
                cidadaos_encontrados=[
                    CidadaoEncontradoOption(**c) for c in lista_cidadaos
                ],
                intencao=payload.intencao
            )
        )

    cidadao = lista_cidadaos[0]

    prontuariogapd_final = normalizar_texto(cidadao.get("prontuariogapd"))
    telefone_final = normalizar_texto(cidadao.get("telefone"))
    nome_final = normalizar_texto(cidadao.get("nome"))

    if payload.intencao == "CONSULTAR_DADOS_CIDADAO":
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=True,
            proxima_acao="EXIBIR_DADOS_CIDADAO",
            mensagem="Cidadão localizado com sucesso.",
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_final,
                nome=nome_final,
                telefone=telefone_final,
                intencao=payload.intencao
            )
        )

    registro_servico = buscar_registro_servico_elegivel_para_continuidade(
        prontuariogapd=prontuariogapd_final,
        telefone=None,
        servicoespecializado=servicoespecializado
    )

    if not registro_servico:
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O cidadão foi identificado, mas não existe registro elegível do serviço informado "
                "para continuidade automática do atendimento."
            ),
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_final,
                nome=nome_final,
                telefone=telefone_final,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado,
                continuidade_atendimento=False
            )
        )

    statusagenda = normalizar_texto(registro_servico.get("statusagenda"))

    if not statusagenda_elegivel_para_continuidade(statusagenda):
        return ConsultarCidadaoAtendimentoResponse(
            sucesso=False,
            proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
            mensagem=(
                "O serviço foi localizado, mas o status atual não permite "
                "continuidade automática do atendimento."
            ),
            dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
                cidadao_identificado=True,
                prontuariogapd=prontuariogapd_final,
                nome=nome_final,
                telefone=telefone_final,
                intencao=payload.intencao,
                servicoespecializado=servicoespecializado,
                continuidade_atendimento=False
            )
        )

    return ConsultarCidadaoAtendimentoResponse(
        sucesso=True,
        proxima_acao="PROSSEGUIR_ATENDIMENTO",
        mensagem="Continuidade validada com sucesso.",
        dados=DadosRetornoConsultarCidadaoAtendimentoResponse(
            cidadao_identificado=True,
            prontuariogapd=prontuariogapd_final,
            nome=nome_final,
            telefone=telefone_final,
            intencao=payload.intencao,
            servicoespecializado=servicoespecializado,
            continuidade_atendimento=True,
            id_notificacao_base=registro_servico["id_notificacao"],
            tipoagenda=normalizar_texto(registro_servico.get("tipoagenda"))
        )
    )