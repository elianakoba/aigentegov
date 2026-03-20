from datetime import datetime

# from app.services.agendamento import gerar_protocolo, validar_idempotencia

from app.db.agendamento import inserir_agendamento_variavel


def criar_agendamento_variavel(payload: dict):
    """
    Regra:
    - Se permite_agente_ia = true  -> status SOLICITADO
    - Se permite_agente_ia = false -> status ENCAMINHADO_HUMANO (registro informativo)
    """

    permite_ia = bool(payload.get("permite_agente_ia", False))

    status = "SOLICITADO" if permite_ia else "ENCAMINHADO_HUMANO"
    motivo = None if permite_ia else "Serviço não permite autoagendamento via IA"

    dados = {
        "tipo_agendamento": "VARIAVEL",
        "status": status,
        "motivo_status": motivo,
        "status_atualizado_em": datetime.now(),

        "data_preferencia_inicio": payload.get("data_preferencia_inicio"),
        "data_preferencia_fim": payload.get("data_preferencia_fim"),
        "diasemana": payload.get("diasemana"),
        "periodo_preferencial": payload.get("periodo_preferencial"),

        "prontuariogapd": payload.get("prontuariogapd"),
        "nome": payload.get("nome"),
        "telefone": payload.get("telefone"),
        "cpf": payload.get("cpf"),

        "servico_id": payload.get("servico_id"),
        "servicoespecializado": payload.get("servicoespecializado"),
        "permite_agente_ia": permite_ia,

        "canal": payload.get("canal", "WHATSAPP"),
        "solicitado_por": payload.get("solicitado_por", "AGENTE_IA"),
        "conversa_id": payload.get("conversa_id"),
        "mensagem_id": payload.get("mensagem_id"),
        "data_agendamento": payload.get("data_agendamento"),
        
        "origem": payload.get("origem"),
        "destino": payload.get("destino"),

        "observacao": payload.get("observacao"),
        "ativo": True,
    }

    return inserir_agendamento_variavel(dados)