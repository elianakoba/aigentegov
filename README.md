# AiGENTEGOV – API de Agendamento e Notificações

API responsável pelo gerenciamento de:

- Agendamentos fixos
- Agendamentos variáveis (eventos / janelas)
- Consultas de dados para Notificações automáticas de lembrete
- Gravação de retorno que pode ser Confirmação, Reagendamento ou cancelamento pelo cidadão

Esta API compõe a camada de serviços do sistema AiGENTEGOV, 
sendo consumida por:

- Agente IA (WhatsApp)
- Sistema Web administrativo
- Serviços institucionais integrados

---

## 🎯 Objetivo

Permitir:

- Criação e gestão de agendamentos
- Validação automática de disponibilidade
- Registro de histórico
- Consulta de dados para Envio de notificações automáticas
- Solicitação de confirmação ao cidadão
- Atualização de status (confirmado, cancelado, reagendado)


## 🔔 Módulo de Notificações

A API possui funcionalidades para:

- Consulta de dados do cidadão e agendamento para possibilitar o Envio automático de lembrete de agendamento pelo agente IA
- Registro de histórico sobre notificação enviada (Grava NOTIFICADO no STATUS de ENVIO) 
- Gravar retorno do cidadadão a respeito do agendamento, registrando a atualização de status do agendamento (confirmado, cancelado, reagendado).

Fluxo simplificado:

Agendamento criado → 
Agente IA utiliza api consulta dados de cidadão e agendas, que precisam ser notificados
Agente IA envia Notificação agendada pelo whats app →  
Cidadão responde →  
Agente IA utiliza API que atualiza status →  
Histórico registrado

### Endpoints relacionados

GET /v1/notificacoes
GET /v1/notificacoes/{id_notificacao}
POST /v1/notificacoes/{id_notificacao}/status




## Módulo de Agendamentos

API responsável pelo gerenciamento de agendamentos fixos (Clínico geral - com slots atendimento pré-fixado por uma grade horária ) e variáveis (ex: Transporte que não utiliza grade horária, o slot de atendimento é fixado no momento da confirmação do agendamento), integrada ao agente inteligente do AiGENTEGOV.

Esta API compõe a camada de serviços do sistema, sendo consumida por:

- Agente IA (atendimento via WhatsApp)
- Sistema Web administrativo
- Integrações institucionais futuras



## 🔄 Fluxo Simplificado – Agendamento

### 1️⃣ Recebimento

O Agente IA recebe mensagem via WhatsApp relacionada a agendamento.

---

### 2️⃣ Identificação da Intenção

A mensagem é classificada como:

- Confirmação de agendamento existente  
- Solicitação de novo agendamento  

---

## 🟢 Caso 1 – Confirmação de Agendamento

1. A API é consultada para obter os dados do cidadão e do agendamento.
2. O Agente IA retorna ao cidadão as informações da agenda.
3. Caso o cidadão confirme ou cancele:
   - A API atualiza o status do agendamento.
   - O histórico é registrado automaticamente.

---

## 🔵 Caso 2 – Solicitação de Novo Agendamento

1. A API é consultada para identificar:
   - Tipo de serviço (agendamento fixo ou evento variável).
   - Regras de disponibilidade.

### 📌 Agendamento Fixo (slot de horário)

1. A API verifica se agenda ativas e elegíveis.
2. A API verifica disponibilidade de horários.
3. O Agente IA apresenta N as opções disponíveis.
4. O cidadão seleciona o horário desejado.
5. A API registra o agendamento e o histórico.
6. O Agente IA confirma o agendamento ao cidadão.

### 📌 Agendamento Variável (evento / janela)

1. A API verifica eventos ativos e elegíveis.
2. O Agente IA confirma solicitação de agendamento
3. O cidadão confirma solicitação.
4. O Agente IA registra solicitação de agenda
6. A API registra o histórico.


---

## 🔔 Pós-Agendamento – Notificação

1. A API agenda o envio automático de lembrete.
2. A notificação solicita confirmação ao cidadão.
3. A resposta recebida atualiza o status do agendamento.
4. Todas as interações são registradas em histórico.


## 🎯 Objetivo

Permitir:
- Consulta Cidadão (por telefone / Id GLPI / CPF)
- Consulta tipo de agendamento de Serviço (Slot Fixo permite ou não agendamento, evento variável permite ou não agendamento)
- Consulta de disponibilidade
- Consulta n datas / horários disponíveis para agendamento de slot fixo
- Gravar agendamentos fixos
- Gravar agendamentos variáveis
- Registro de histórico 
- Gravar registro no sistema legado (Integração com sistema GLPD de transporte)

---

## 🏗 Arquitetura

**Stack atual:**

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Uvicorn
- AWS (RDS / EC2 – ambiente futuro)

Arquitetura simplificada:

Agente IA → API FastAPI → Banco PostgreSQL

---

## 🔐 Autenticação

A API utiliza autenticação via API Key.

Header obrigatório:

Authorization: Bearer SUA_API_KEY

Caso o header não seja informado:


