# AiGENTEGOV – API de Agendamento e Notificações

API responsável pelo gerenciamento de agendamentos fixos e variáveis, bem como pela consulta e atualização de dados relacionados a notificações de agendamento.

Esta API compõe a camada de serviços do sistema AiGENTEGOV e é consumida por:

- Agente IA (WhatsApp)
- Sistema Web administrativo
- Integrações institucionais futuras

---

## Objetivo

Permitir:

- Identificação do cidadão (por telefone, CPF ou identificador institucional)
- Verificação se o serviço permite agendamento automatizado via Agente IA
- Consulta de disponibilidade para serviços com slot fixo
- Registro de agendamentos fixos
- Registro de solicitações de agendamentos variáveis
- Consulta de agendamentos existentes
- Atualização de status do agendamento (confirmado, cancelado, reagendado)
- Integração com sistema legado (ex.: sistema de transporte)

---

## Módulo de Agendamentos

A API gerencia dois tipos de agendamento:

### 1. Agendamento Fixo

Utiliza grade horária previamente definida, com slots de atendimento configurados por:

- Serviço
- Profissional
- Unidade

Exemplo: atendimento clínico geral com horários previamente configurados por especialista.

Características:

- Necessita consulta prévia de disponibilidade
- Reserva efetiva de slot
- Controle de concorrência para evitar dupla ocupação

---

### 2. Agendamento Variável

Não utiliza grade horária fixa.

A solicitação é registrada e a confirmação ocorre posteriormente, podendo depender de análise interna ou disponibilidade operacional.

Exemplos:

- Transporte
- Eventos com janela flexível
- Serviços sujeitos a aprovação

Características:

- Registro inicial como "Solicitado"
- Confirmação posterior com atualização de status

---

## Parametrização de Serviço

Cada serviço possui configuração que define:

- Permite agendamento automatizado via Agente IA
- Não permite agendamento automatizado via Agente IA

### Quando o serviço NÃO permite agendamento via IA

- O Agente IA informa o cidadão
- A API registra a solicitação como atendimento informativo
- O fluxo é encaminhado para atendimento humano

---

## Fluxo Simplificado de Agendamento

### 1. Recebimento da Solicitação

O Agente IA recebe mensagem via WhatsApp relacionada a agendamento.

### 2. Identificação da Intenção

A mensagem é classificada como:

- Novo agendamento
- Consulta de agendamento existente

---

## Caso A — Novo Agendamento

### Etapa 1 — Identificação do Serviço

A API é consultada para identificar:

- Se o serviço permite agendamento via Agente IA
- O tipo do serviço (Fixo ou Variável)

---

### Etapa 2 — Verificação de Permissão

#### Se NÃO permite agendamento via IA:

- O Agente IA informa o cidadão
- A API registra a interação
- O fluxo é direcionado para atendimento humano

#### Se permite agendamento via IA:

O fluxo segue conforme o tipo do serviço.

---

### Fluxo — Agendamento Fixo

1. A API verifica agendas ativas e elegíveis
2. A API calcula e retorna os horários disponíveis
3. O Agente IA apresenta as opções ao cidadão
4. O cidadão seleciona o horário desejado
5. A API valida novamente a disponibilidade (controle de concorrência)
6. A API registra o agendamento
7. O Agente IA confirma o agendamento ao cidadão
8. O histórico da operação é registrado automaticamente

---

### Fluxo — Agendamento Variável

1. O Agente IA confirma os dados da solicitação
2. A API registra a solicitação com status inicial "Solicitado"
3. O Agente IA confirma o recebimento ao cidadão
4. Posteriormente, o status pode ser atualizado para:
   - Confirmado
   - Cancelado
   - Reagendado

---

## Caso B — Consulta de Agendamento Existente

1. O cidadão solicita informações sobre agendamento existente
2. A API consulta agendamentos vinculados ao identificador informado
3. A API retorna:
   - Data
   - Hora (se aplicável)
   - Tipo de serviço
   - Status atual
4. O Agente IA apresenta as informações ao cidadão

---

## Endpoints Principais

### Agendamento


# Dicionário de Dados — AiGENTEGOV (MVP)

Este dicionário descreve as duas tabelas principais utilizadas no MVP de agendamento:

- `public.gradeagenda_slotfixo`: representa a **oferta** (grade/slots) de agenda fixa.
- `public.agendamento`: representa a **demanda/reserva** (agendamentos fixos e solicitações variáveis).

---

## Tabela: `public.gradeagenda_slotfixo`

### Finalidade
Armazenar a grade horária (slots) de serviços com **agendamento fixo**, permitindo consultar disponibilidade e reservar/bloquear horários.

### Campos

| Campo | Tipo | Nulo | Padrão | Descrição |
|---|---|---:|---|---|
| `id_slot` | `bigint` (identity) | Não | — | Identificador único do slot fixo. |
| `servico_id` | `bigint` | Não | — | Identificador do serviço associado ao slot. |
| `servico_nome` | `varchar(120)` | Sim | — | Nome do serviço (uso auxiliar/relatórios). |
| `unidade_id` | `bigint` | Sim | — | Identificador da unidade (quando aplicável). |
| `profissional_id` | `bigint` | Sim | — | Identificador do profissional (quando aplicável). |
| `inicio_em` | `timestamptz` | Não | — | Data/hora de início do slot (com fuso). |
| `fim_em` | `timestamptz` | Sim | — | Data/hora de término do slot (com fuso). |
| `status_slot` | `varchar(12)` | Não | `LIVRE` | Situação do slot: `LIVRE`, `RESERVADO` ou `BLOQUEADO`. |
| `ativo` | `boolean` | Não | `true` | Indica se o slot está ativo para uso. |
| `criado_em` | `timestamptz` | Não | `now()` | Data/hora de criação do registro. |
| `atualizado_em` | `timestamptz` | Não | `now()` | Data/hora da última atualização do registro. |

### Regras e Observações
- Um slot representa um horário de atendimento na grade (oferta).
- O slot pode ser:
  - `LIVRE`: disponível para reserva
  - `RESERVADO`: vinculado a um agendamento fixo (ou em processo de reserva)
  - `BLOQUEADO`: indisponível (ex.: pausa, manutenção, bloqueio administrativo)

### Índices e Restrições
- `ux_gradeagenda_slotfixo_unique` (UNIQUE): evita duplicidade do mesmo slot por `(servico_id, inicio_em, unidade_id, profissional_id)`.
- `idx_gradeagenda_slotfixo_status_inicio`: acelera busca por disponibilidade (status + início).
- `idx_gradeagenda_slotfixo_servico_inicio`: acelera busca por serviço em janelas de tempo.

---

## Tabela: `public.agendamento`

### Finalidade
Armazenar os agendamentos realizados (fixos) e as solicitações de agendamento (variáveis), incluindo status, dados do cidadão e rastreabilidade da operação.

### Campos

| Campo | Tipo | Nulo | Padrão | Descrição |
|---|---|---:|---|---|
| `id_agendamento` | `bigint` (identity) | Não | — | Identificador único do agendamento. |
| `tipo_agendamento` | `varchar(10)` | Não | — | Tipo do agendamento: `FIXO` ou `VARIAVEL`. |
| `status` | `varchar(30)` | Não | `SOLICITADO` | Status do processo: `SOLICITADO`, `CONFIRMADO`, `CANCELADO`, `REAGENDADO`, `CONCLUIDO`, `NAO_PERMITE_IA`, `ENCAMINHADO_HUMANO`. |
| `motivo_status` | `text` | Sim | — | Motivo/justificativa do status (quando aplicável). |
| `status_atualizado_em` | `timestamptz` | Sim | — | Data/hora da última atualização de status. |
| `inicio_em` | `timestamptz` | Sim | — | Data/hora do agendamento (principalmente para FIXO). |
| `fim_em` | `timestamptz` | Sim | — | Data/hora fim do agendamento (principalmente para FIXO). |
| `data_preferencia_inicio` | `date` | Sim | — | Início da janela preferencial (principalmente para VARIAVEL). |
| `data_preferencia_fim` | `date` | Sim | — | Fim da janela preferencial (principalmente para VARIAVEL). |
| `diasemana` | `smallint` | Sim | — | Dia da semana preferencial (0=domingo … 6=sábado). |
| `periodo_preferencial` | `varchar(10)` | Sim | — | Período preferencial: `MANHA`, `TARDE` ou `NOITE`. |
| `prontuariogapd` | `integer` | Sim | — | Identificador institucional/prontuário (quando existir). |
| `nome` | `varchar(150)` | Sim | — | Nome informado/identificado do cidadão. |
| `telefone` | `varchar(50)` | Sim | — | Telefone (ex.: WhatsApp) utilizado para identificação/contato. |
| `cpf` | `varchar(14)` | Sim | — | CPF do cidadão (quando informado). |
| `servico_id` | `bigint` | Sim | — | Identificador do serviço (preferível ao nome). |
| `servico_nome` | `varchar(120)` | Sim | — | Nome do serviço (uso auxiliar/relatórios). |
| `permite_agente_ia` | `boolean` | Não | `false` | Indica se o serviço permite autoagendamento via Agente IA. |
| `canal` | `varchar(20)` | Não | `WHATSAPP` | Canal de entrada: ex.: `WHATSAPP`, `WEB`, `API`, `HUMANO`. |
| `solicitado_por` | `varchar(50)` | Não | `AGENTE_IA` | Origem lógica do registro: ex.: `AGENTE_IA`, `USUARIO_WEB`. |
| `conversa_id` | `varchar(80)` | Sim | — | Identificador da conversa (rastreamento WhatsApp). |
| `mensagem_id` | `varchar(80)` | Sim | — | Identificador da mensagem (rastreamento WhatsApp). |
| `chave_idempotencia` | `varchar(80)` | Sim | — | Chave para evitar duplicidade (reprocessamento/reenvio). |
| `protocolo` | `varchar(30)` | Sim | — | Código de protocolo para comunicação com o cidadão. |
| `id_slot` | `bigint` | Sim | — | FK para `gradeagenda_slotfixo.id_slot` (quando FIXO e vinculado a um slot). |
| `origem` | `varchar(80)` | Sim | — | Origem do deslocamento (quando transporte/variável). |
| `destino` | `varchar(80)` | Sim | — | Destino do deslocamento (quando transporte/variável). |
| `observacao` | `text` | Sim | — | Observações gerais do atendimento/agendamento. |
| `ativo` | `boolean` | Não | `true` | Indica se o registro está ativo. |
| `criado_em` | `timestamptz` | Não | `now()` | Data/hora de criação do registro. |
| `atualizado_em` | `timestamptz` | Não | `now()` | Data/hora da última atualização do registro. |

### Regras e Observações
- **Agendamento FIXO**
  - Deve utilizar `inicio_em`/`fim_em`.
  - Pode vincular `id_slot` (quando o slot foi reservado/confirmado).
- **Agendamento VARIÁVEL**
  - Pode utilizar `data_preferencia_inicio`/`data_preferencia_fim` e/ou `periodo_preferencial`.
  - Pode não possuir `inicio_em` no momento da solicitação (até confirmação posterior).
- **Serviço não permite IA**
  - Recomenda-se registrar com `permite_agente_ia=false` e `status='ENCAMINHADO_HUMANO'` ou `status='NAO_PERMITE_IA'`.

### Índices e Restrições
- `fk_agendamento_slotfixo`: FK opcional para o slot fixo (`id_slot`).
- `ux_agendamento_idempotencia` (UNIQUE parcial): garante que `chave_idempotencia` não se repita quando informada.
- Índices auxiliares: `status`, `telefone`, `cpf`, `servico_id`.

---