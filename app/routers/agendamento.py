from datetime import time
from fastapi import APIRouter, HTTPException, Depends, status, Body

from app.core.security import validar_api_key
from app.schemas.agendamento import (
    AgendamentoRequest,
    AgendamentoResponse,
    DadosRetornoAgendamentoResponse,
    OpcaoDisponivelResponse
)
from app.db.agendamento import (
    buscar_notificacao_por_id,
    buscar_slots_disponiveis,
    buscar_slots_alternativos,
    inserir_notificacao_agendamento,
    registrar_agendamento_slot_fixo
)


router = APIRouter(
    prefix="/v1/agendamentos",
    tags=["Agendamentos"],
    dependencies=[Depends(validar_api_key)]
)


def eh_servico_transporte(servicoespecializado: str | None) -> bool:
    if not servicoespecializado:
        return False
    return "TRANSPORTE" in servicoespecializado.strip().upper()


def resolver_servicoespecializado(payload: AgendamentoRequest, notificacao_base: dict) -> str | None:
    """
    Prioriza o serviço informado no payload.
    Se não vier, tenta aproveitar o que existir na notificação-base.
    """
    return payload.servicoespecializado or notificacao_base.get("servicoespecializado")


def resolver_tipoagenda(notificacao_base: dict) -> str | None:
    """
    Nesta versão, a API continua usando o tipoagenda já disponível
    na notificação-base, pois ainda não foi acoplada a uma
    parametrização central de serviços.
    """
    return notificacao_base.get("tipoagenda")


def formatar_hora(valor) -> str | None:
    """
    Converte time/str para HH:MM.
    Evita erro de serialização/validação na response model.
    """
    if valor is None:
        return None
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if hasattr(valor, "strftime"):
        return valor.strftime("%H:%M")
    return str(valor)[:5]


def montar_dados_retorno(
    *,
    id_notificacao_base: int,
    registro: dict | None = None,
    tipoagenda: str | None = None,
    id_slot: int | None = None,
    opcoes_disponiveis=None,
    campos_pendentes=None
) -> DadosRetornoAgendamentoResponse:
    if not registro:
        return DadosRetornoAgendamentoResponse(
            id_notificacao_base=id_notificacao_base,
            tipoagenda=tipoagenda,
            id_slot=id_slot,
            opcoes_disponiveis=opcoes_disponiveis,
            campos_pendentes=campos_pendentes
        )

    return DadosRetornoAgendamentoResponse(
        id_notificacao_base=id_notificacao_base,
        id_notificacao_agendamento=registro.get("id_notificacao"),
        tipoagenda=registro.get("tipoagenda") or tipoagenda,
        situacaonotificacao=registro.get("situacaonotificacao"),
        statusagenda=registro.get("statusagenda"),
        dataagendamento=registro.get("dataagendamento"),
        horaagendamento=formatar_hora(registro.get("horaagendamento")),
        datapreferencia=registro.get("datapreferencia"),
        horapreferencia=formatar_hora(registro.get("horapreferencia")),
        datasolicitacao=registro.get("datasolicitacao"),
        dataautorizacao=registro.get("dataautorizacao"),
        origem=registro.get("origem"),
        destino=registro.get("destino"),
        id_slot=id_slot,
        opcoes_disponiveis=opcoes_disponiveis,
        campos_pendentes=campos_pendentes
    )


@router.post(
    "",
    response_model=AgendamentoResponse,
    summary="Realizar agendamento",
    description=(
        "Endpoint principal do fluxo de agendamento.\n\n"
        "OBJETIVO:\n"
        "Esta API trata a solicitação de agendamento a partir de uma notificação-base "
        "já localizada anteriormente. O cidadão não é identificado aqui do zero. "
        "A API usa a notificação-base para obter os dados do cidadão e decidir "
        "como processar o fluxo do serviço.\n\n"

        "REGRAS GERAIS:\n"
        "1. O campo id_notificacao_base é obrigatório em qualquer chamada.\n"
        "2. O agente deve sempre chamar esta única rota, sem tentar decidir por conta própria "
        "se o fluxo é transporte, evento_variavel ou slot_fixo.\n"
        "3. A API decide internamente o comportamento e devolve a orientação em proxima_acao.\n"
        "4. datapreferencia e horapreferencia representam a intenção do cidadão.\n"
        "5. dataagendamento e horaagendamento representam apenas confirmação efetiva do atendimento.\n"
        "6. id_slot só deve ser enviado quando o serviço for do tipo slot_fixo e a própria API "
        "já tiver retornado opções para escolha.\n\n"

        "COMPORTAMENTOS POSSÍVEIS:\n"
        "- Se não existir notificação-base válida: ENCAMINHAR_ATENDENTE_HUMANO.\n"
        "- Se faltarem dados obrigatórios: INFORMAR_DADOS_OBRIGATORIOS.\n"
        "- Se for transporte: registra solicitação pendente de aprovação e orienta encaminhamento ao atendente humano.\n"
        "- Se for evento_variavel: registra a solicitação e retorna AGENDAMENTO_REGISTRADO.\n"
        "- Se for slot_fixo sem id_slot: consulta disponibilidade e retorna opções ou indisponibilidade.\n"
        "- Se for slot_fixo com id_slot: conclui o agendamento e retorna AGENDAMENTO_REALIZADO.\n\n"

        "INTERPRETAÇÃO DE proxima_acao:\n"
        "- AGENDAMENTO_REGISTRADO: solicitação criada com sucesso, sem vaga efetivamente confirmada.\n"
        "- AGENDAMENTO_REALIZADO: vaga efetivamente reservada.\n"
        "- SELECIONAR_OPCAO_DISPONIVEL: a API retornou opções e o cidadão deve escolher uma.\n"
        "- INFORMAR_DADOS_OBRIGATORIOS: faltam campos para continuar.\n"
        "- SEM_DISPONIBILIDADE: não há vagas compatíveis com os critérios informados.\n"
        "- ENCAMINHAR_ATENDENTE_HUMANO: o fluxo deve sair do autoatendimento.\n\n"

        "OBSERVAÇÃO IMPORTANTE:\n"
        "No fluxo conversacional normal, o agente não deve enviar dataagendamento e horaagendamento "
        "para solicitar atendimento. Deve usar datapreferencia e horapreferencia."
    )
)
def criar_agendamento(
    payload: AgendamentoRequest = Body(
        ...,
        openapi_examples={
            "transporte_completo": {
                "summary": "Transporte - solicitação completa",
                "description": (
                    "Usar quando o serviço for transporte. "
                    "A API registrará a solicitação como pendente de aprovação "
                    "e orientará encaminhamento ao atendente humano."
                ),
                "value": {
                    "id_notificacao_base": 10,
                    "servicoespecializado": "TRANSPORTE",
                    "datapreferencia": "2026-03-20",
                    "horapreferencia": "09:00",
                    "origem": "Residência",
                    "destino": "Hospital Municipal",
                    "observacaonotificacao": "Solicitação recebida via WhatsApp"
                }
            },
            "transporte_incompleto": {
                "summary": "Transporte - faltando dados",
                "description": (
                    "Exemplo propositalmente incompleto. "
                    "A API deverá retornar proxima_acao = INFORMAR_DADOS_OBRIGATORIOS."
                ),
                "value": {
                    "id_notificacao_base": 10,
                    "servicoespecializado": "TRANSPORTE",
                    "datapreferencia": "2026-03-20"
                }
            },
            "evento_variavel_completo": {
                "summary": "Evento variável - solicitação completa",
                "description": (
                    "Usar quando o serviço for do tipo evento_variavel. "
                    "A API registrará a solicitação do cidadão."
                ),
                "value": {
                    "id_notificacao_base": 20,
                    "servicoespecializado": "FISIOTERAPIA_DOMICILIAR",
                    "datapreferencia": "2026-03-21",
                    "horapreferencia": "08:30",
                    "observacaonotificacao": "Solicitação inicial do cidadão"
                }
            },
            "evento_variavel_herdando_servico": {
                "summary": "Evento variável - usando serviço da notificação-base",
                "description": (
                    "Quando servicoespecializado já estiver presente na notificação-base, "
                    "o payload pode omitir esse campo."
                ),
                "value": {
                    "id_notificacao_base": 20,
                    "datapreferencia": "2026-03-21",
                    "horapreferencia": "08:30",
                    "observacaonotificacao": "Usar serviço herdado da notificação-base"
                }
            },
            "slot_fixo_consulta_data": {
                "summary": "Slot fixo - consultar disponibilidade por data",
                "description": (
                    "Usar quando o cidadão deseja consultar horários disponíveis "
                    "para uma determinada data."
                ),
                "value": {
                    "id_notificacao_base": 30,
                    "servicoespecializado": "FISIOTERAPIA",
                    "datapreferencia": "2026-03-22",
                    "observacaonotificacao": "Consultar horários disponíveis"
                }
            },
            "slot_fixo_consulta_data_hora": {
                "summary": "Slot fixo - consultar disponibilidade por data e hora",
                "description": (
                    "Usar quando o cidadão informar uma preferência de data e também de horário. "
                    "A API tentará encontrar a vaga exata e, se não houver, poderá devolver alternativas."
                ),
                "value": {
                    "id_notificacao_base": 30,
                    "servicoespecializado": "FISIOTERAPIA",
                    "datapreferencia": "2026-03-22",
                    "horapreferencia": "10:00",
                    "observacaonotificacao": "Cidadão prefere atendimento às 10h"
                }
            },
            "slot_fixo_confirmacao": {
                "summary": "Slot fixo - confirmar opção escolhida",
                "description": (
                    "Usar somente após a API já ter devolvido opções em opcoes_disponiveis "
                    "e o cidadão ter escolhido uma delas."
                ),
                "value": {
                    "id_notificacao_base": 30,
                    "servicoespecializado": "FISIOTERAPIA",
                    "id_slot": 5,
                    "observacaonotificacao": "Cidadão confirmou a opção escolhida"
                }
            },
            "slot_fixo_confirmacao_com_preferencia": {
                "summary": "Slot fixo - confirmar opção escolhida com preferência registrada",
                "description": (
                    "Também pode ser usado quando se deseja manter, por histórico, "
                    "a data e hora preferidas originalmente informadas pelo cidadão."
                ),
                "value": {
                    "id_notificacao_base": 30,
                    "servicoespecializado": "FISIOTERAPIA",
                    "id_slot": 5,
                    "datapreferencia": "2026-03-22",
                    "horapreferencia": "10:00",
                    "observacaonotificacao": "Confirmar slot escolhido"
                }
            }
        }
    )
):
    try:
        # ======================================================
        # 1) CONSULTA A NOTIFICACAO-BASE
        # ======================================================
        notificacao_base = buscar_notificacao_por_id(payload.id_notificacao_base)

        if not notificacao_base:
            return AgendamentoResponse(
                sucesso=False,
                proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
                mensagem=(
                    "Não foi localizada notificação-base válida para iniciar o autoagendamento. "
                    "O caso deve ser encaminhado ao atendente humano."
                ),
                dados=montar_dados_retorno(
                    id_notificacao_base=payload.id_notificacao_base
                )
            )

        servicoespecializado = resolver_servicoespecializado(payload, notificacao_base)
        tipoagenda = resolver_tipoagenda(notificacao_base)

        campos_pendentes = []

        if not servicoespecializado:
            campos_pendentes.append("servicoespecializado")

        if not tipoagenda:
            campos_pendentes.append("tipoagenda")

        if campos_pendentes:
            return AgendamentoResponse(
                sucesso=False,
                proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
                mensagem="Faltam dados obrigatórios para identificar o fluxo do serviço.",
                dados=montar_dados_retorno(
                    id_notificacao_base=payload.id_notificacao_base,
                    campos_pendentes=campos_pendentes
                )
            )

        # ======================================================
        # 2) REGRA ESPECIAL PARA TRANSPORTE
        # ======================================================
        if eh_servico_transporte(servicoespecializado):
            campos_pendentes = []

            if not payload.datapreferencia:
                campos_pendentes.append("datapreferencia")

            if not payload.horapreferencia:
                campos_pendentes.append("horapreferencia")

            if not payload.origem:
                campos_pendentes.append("origem")

            if not payload.destino:
                campos_pendentes.append("destino")

            if campos_pendentes:
                return AgendamentoResponse(
                    sucesso=False,
                    proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
                    mensagem=(
                        "Faltam dados obrigatórios para registrar a solicitação de transporte "
                        "como pendente de aprovação."
                    ),
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        tipoagenda=tipoagenda,
                        campos_pendentes=campos_pendentes
                    )
                )

            registro = inserir_notificacao_agendamento(
                notificacao_base=notificacao_base,
                servicoespecializado=servicoespecializado,
                tipoagenda=tipoagenda,
                origem=payload.origem,
                destino=payload.destino,
                dataagendamento=None,
                horaagendamento=None,
                situacaonotificacao="PENDENTE_APROVACAO",
                observacaonotificacao=payload.observacaonotificacao,
                statusagenda="SOLICITADO",
                datapreferencia=payload.datapreferencia,
                horapreferencia=payload.horapreferencia,
                datasolicitacao=payload.datasolicitacao,
                dataautorizacao=payload.dataautorizacao
            )

            return AgendamentoResponse(
                sucesso=True,
                proxima_acao="ENCAMINHAR_ATENDENTE_HUMANO",
                mensagem=(
                    "Solicitação de transporte registrada como pendente de aprovação. "
                    "O atendimento deve seguir para o atendente humano."
                ),
                dados=montar_dados_retorno(
                    id_notificacao_base=payload.id_notificacao_base,
                    registro=registro
                )
            )

        # ======================================================
        # 3) FLUXO PARA EVENTO_VARIAVEL
        # ======================================================
        if tipoagenda == "evento_variavel":
            campos_pendentes = []

            if not payload.datapreferencia:
                campos_pendentes.append("datapreferencia")

            if not payload.horapreferencia:
                campos_pendentes.append("horapreferencia")

            if campos_pendentes:
                return AgendamentoResponse(
                    sucesso=False,
                    proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
                    mensagem="Faltam dados obrigatórios para registrar a solicitação do tipo evento_variavel.",
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        tipoagenda="evento_variavel",
                        campos_pendentes=campos_pendentes
                    )
                )

            registro = inserir_notificacao_agendamento(
                notificacao_base=notificacao_base,
                servicoespecializado=servicoespecializado,
                tipoagenda=tipoagenda,
                origem=payload.origem,
                destino=payload.destino,
                dataagendamento=None,
                horaagendamento=None,
                situacaonotificacao="SOLICITADO",
                observacaonotificacao=payload.observacaonotificacao,
                statusagenda="SOLICITADO",
                datapreferencia=payload.datapreferencia,
                horapreferencia=payload.horapreferencia,
                datasolicitacao=payload.datasolicitacao,
                dataautorizacao=payload.dataautorizacao
            )

            return AgendamentoResponse(
                sucesso=True,
                proxima_acao="AGENDAMENTO_REGISTRADO",
                mensagem="Solicitação registrada com sucesso.",
                dados=montar_dados_retorno(
                    id_notificacao_base=payload.id_notificacao_base,
                    registro=registro
                )
            )

        # ======================================================
        # 4) FLUXO PARA SLOT_FIXO
        # ======================================================
        if tipoagenda == "slot_fixo":
            if payload.id_slot is not None:
                resultado = registrar_agendamento_slot_fixo(
                    notificacao_base=notificacao_base,
                    id_slot=payload.id_slot,
                    servicoespecializado=servicoespecializado,
                    tipoagenda=tipoagenda,
                    origem=payload.origem,
                    destino=payload.destino,
                    observacaonotificacao=payload.observacaonotificacao,
                    datapreferencia=payload.datapreferencia,
                    horapreferencia=payload.horapreferencia,
                    datasolicitacao=payload.datasolicitacao,
                    dataautorizacao=payload.dataautorizacao
                )

                notificacao_agendamento = resultado["notificacao"]
                slot = resultado["slot"]

                return AgendamentoResponse(
                    sucesso=True,
                    proxima_acao="AGENDAMENTO_REALIZADO",
                    mensagem="Agendamento realizado com sucesso.",
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        registro=notificacao_agendamento,
                        id_slot=slot["id_slot"]
                    )
                )

            data_consulta = payload.datapreferencia
            hora_consulta = payload.horapreferencia

            campos_pendentes = []
            if not data_consulta:
                campos_pendentes.append("datapreferencia")

            if campos_pendentes:
                return AgendamentoResponse(
                    sucesso=False,
                    proxima_acao="INFORMAR_DADOS_OBRIGATORIOS",
                    mensagem="Faltam dados obrigatórios para consultar disponibilidade do serviço do tipo slot_fixo.",
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        tipoagenda="slot_fixo",
                        campos_pendentes=campos_pendentes
                    )
                )

            slots = buscar_slots_disponiveis(
                servicoespecializado=servicoespecializado,
                dataagendamento=data_consulta,
                horaagendamento=hora_consulta
            )

            if slots:
                opcoes = [
                    OpcaoDisponivelResponse(
                        id_slot=slot["id_slot"],
                        dataagendamento=slot["dataagenda"],
                        horaagendamento=formatar_hora(slot["horaagenda"]),
                        unidade=slot["unidade"],
                        servicoespecializado=slot["servicoespecializado"]
                    )
                    for slot in slots
                ]

                return AgendamentoResponse(
                    sucesso=True,
                    proxima_acao="SELECIONAR_OPCAO_DISPONIVEL",
                    mensagem="Foram encontradas opções de horário para o serviço solicitado.",
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        tipoagenda="slot_fixo",
                        opcoes_disponiveis=opcoes
                    )
                )

            alternativas = buscar_slots_alternativos(
                servicoespecializado=servicoespecializado,
                dataagendamento=data_consulta,
                horaagendamento=hora_consulta
            )

            if alternativas:
                opcoes = [
                    OpcaoDisponivelResponse(
                        id_slot=slot["id_slot"],
                        dataagendamento=slot["dataagenda"],
                        horaagendamento=formatar_hora(slot["horaagenda"]),
                        unidade=slot["unidade"],
                        servicoespecializado=slot["servicoespecializado"]
                    )
                    for slot in alternativas
                ]

                return AgendamentoResponse(
                    sucesso=True,
                    proxima_acao="SELECIONAR_OPCAO_DISPONIVEL",
                    mensagem="Não há vaga exata na data solicitada, mas existem alternativas disponíveis.",
                    dados=montar_dados_retorno(
                        id_notificacao_base=payload.id_notificacao_base,
                        tipoagenda="slot_fixo",
                        opcoes_disponiveis=opcoes
                    )
                )

            return AgendamentoResponse(
                sucesso=False,
                proxima_acao="SEM_DISPONIBILIDADE",
                mensagem="Não há horários disponíveis para os critérios informados.",
                dados=montar_dados_retorno(
                    id_notificacao_base=payload.id_notificacao_base,
                    tipoagenda="slot_fixo"
                )
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor de tipoagenda é inválido. Use evento_variavel ou slot_fixo."
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar agendamento: {str(e)}"
        )