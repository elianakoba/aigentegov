from datetime import time
from fastapi import APIRouter, HTTPException, Depends, status

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
        status_agenda=registro.get("status_agenda"),
        dataagendamento=registro.get("dataagendamento"),
        horaagendamento=formatar_hora(registro.get("horaagendamento")),
        data_preferencia=registro.get("data_preferencia"),
        hora_preferencia=formatar_hora(registro.get("hora_preferencia")),
        data_solicitacao=registro.get("data_solicitacao"),
        data_autorizacao=registro.get("data_autorizacao"),
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
        "Endpoint principal para tratamento do fluxo de agendamento. "
        "Esta API pressupõe que o cidadão já foi previamente identificado "
        "por telefone ou prontuário em uma etapa anterior, e que uma "
        "notificação-base válida já foi localizada. "
        "A API consulta essa notificação para obter os dados do cidadão e, "
        "quando necessário, cria um novo registro para representar "
        "a solicitação ou o agendamento. "
        "Para serviços com evento_variavel, registra a solicitação do cidadão. "
        "Para serviços com slot_fixo, consulta a disponibilidade quando necessário, "
        "retorna opções ao agente e conclui o agendamento quando um slot é informado. "
        "Se não existir nenhuma notificação-base válida sobre o serviço, a API orienta "
        "encaminhamento ao atendente humano. "
        "Para serviços de transporte, a API registra a solicitação como pendente de aprovação "
        "e orienta encaminhamento ao atendente humano. "
        "Na fase de solicitação, os campos data_preferencia e hora_preferencia representam "
        "o desejo informado pelo cidadão. Os campos dataagendamento e horaagendamento "
        "devem representar apenas o atendimento efetivamente confirmado."
    )
)
def criar_agendamento(payload: AgendamentoRequest):
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

            if not payload.data_preferencia:
                campos_pendentes.append("data_preferencia")

            if not payload.hora_preferencia:
                campos_pendentes.append("hora_preferencia")

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
                status_agenda="SOLICITADO",
                data_preferencia=payload.data_preferencia,
                hora_preferencia=payload.hora_preferencia,
                data_solicitacao=payload.data_solicitacao,
                data_autorizacao=payload.data_autorizacao
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

            if not payload.data_preferencia:
                campos_pendentes.append("data_preferencia")

            if not payload.hora_preferencia:
                campos_pendentes.append("hora_preferencia")

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
                status_agenda="SOLICITADO",
                data_preferencia=payload.data_preferencia,
                hora_preferencia=payload.hora_preferencia,
                data_solicitacao=payload.data_solicitacao,
                data_autorizacao=payload.data_autorizacao
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
                    data_preferencia=payload.data_preferencia,
                    hora_preferencia=payload.hora_preferencia,
                    data_solicitacao=payload.data_solicitacao,
                    data_autorizacao=payload.data_autorizacao
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

            data_consulta = payload.data_preferencia
            hora_consulta = payload.hora_preferencia

            campos_pendentes = []
            if not data_consulta:
                campos_pendentes.append("data_preferencia")

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