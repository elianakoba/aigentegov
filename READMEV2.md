# AiGENTEGOV – API de Agendamento e Notificações

API responsável pelo gerenciamento de agendamentos fixos e variáveis, bem como pela consulta e atualização de dados relacionados a notificações de agendamento.

Esta API compõe a camada de serviços do sistema AiGENTEGOV e é consumida por:

- Agente IA (WhatsApp)
- Sistema Web administrativo
- Integrações institucionais futuras


## Objetivo

Permitir:

- Consulta de cidadão (por telefone, CPF ou identificador institucional)
- Identificação do tipo de agendamento associado a um serviço
- Verificação se o serviço permite agendamento automatizado via Agente IA
- Consulta de disponibilidade
- Consulta de múltiplas datas e horários disponíveis para agendamento de slot fixo
- Registro de agendamentos fixos
- Registro de agendamentos variáveis
- Atualização de status do agendamento (confirmado, cancelado, reagendado)
- Registro automático de histórico
- Integração com sistema legado (ex.: sistema de transporte)


## Módulo de Agendamentos

API responsável pelo gerenciamento de dois tipos de agendamento:

### Agendamento Fixo

Utiliza grade horária previamente definida, com slots de atendimento configurados por serviço, profissional ou unidade.

Exemplo: atendimento clínico geral, que tem uma grade horária do serviço para cada especialista que atende determinado serviço.

### Agendamento Variável

Não utiliza grade horária fixa. O horário ou condição de atendimento pode ser definido no momento da confirmação ou conforme regra específica do serviço.

Exemplo: transporte ou eventos com janela flexível.


## Parametrização de Serviço

Os serviços podem estar configurados como:

- Permite agendamento automatizado via Agente IA
- Não permite agendamento automatizado

Caso o serviço não permita agendamento via IA:

- O Agente IA informa ao cidadão a indisponibilidade de autoagendamento.
- O atendimento é encaminhado para fluxo humano.
- Nenhum registro automático de agendamento é criado.
- Registro da solicitação é registrado no histórico.


## Fluxo Simplificado – Agendamento

### 1. Recebimento

O Agente IA recebe mensagem via WhatsApp relacionada a agendamento.

### 2. Identificação da Intenção

A mensagem é classificada como:

- Confirmação de agendamento existente
- Solicitação de novo agendamento


### Caso 1 – Confirmação de Agendamento

1. A API é consultada para obter dados do cidadão e do agendamento.
2. O Agente IA retorna as informações ao cidadão.
3. Caso o cidadão confirme, cancele ou solicite reagendamento:
   - A API atualiza o status do agendamento.
   - O histórico é registrado automaticamente.


### Caso 2 – Solicitação de Novo Agendamento

1. A API é consultada para identificar:
   - Tipo de serviço (slot fixo ou evento variável)
   - Se o serviço permite agendamento automatizado
   - Regras de elegibilidade e disponibilidade

2. Caso o serviço não permita agendamento via IA:
   - O Agente IA informa o cidadão.
   - O atendimento é encaminhado para fluxo humano.

3. Caso o serviço permita agendamento via IA:
   - O fluxo segue conforme o tipo de agendamento.


#### Agendamento Fixo

1. A API verifica agendas ativas e elegíveis.
2. A API retorna os horários disponíveis.
3. O Agente IA apresenta as opções ao cidadão.
4. O cidadão seleciona o horário desejado.
5. A API registra o agendamento.
6. O histórico é registrado automaticamente.
7. O Agente IA confirma o agendamento ao cidadão.


#### Agendamento Variável

1. A API verifica eventos ativos e elegíveis.
2. O Agente IA apresenta as opções disponíveis.
3. O cidadão confirma participação ou solicitação.
4. A API registra a inscrição ou solicitação.
5. O histórico é registrado automaticamente.
6. O Agente IA confirma a inscrição ao cidadão.


## Módulo de Notificações

A API possui funcionalidades para:

- Consulta de agendamentos elegíveis para notificação
- Registro de envio de notificação
- Registro do retorno do cidadão e da atualização do status do agendamento
- Registro de histórico das interações


## Fluxo Simplificado – Notificação

1. Um agendamento é criado ou identificado como elegível para notificação.
2. A API disponibiliza os agendamentos a serem notificados.
3. O Agente IA consulta a API.
4. O Agente IA envia lembrete via WhatsApp.
5. O cidadão responde.
6. O Agente IA envia a resposta para a API.
7. A API atualiza o status do agendamento.
8. O histórico é registrado automaticamente.


## Endpoints Relacionados

Notificações:

GET /v1/notificacoes  
GET /v1/notificacoes/{id_notificacao}  
POST /v1/notificacoes/{id_notificacao}/status  

Agendamentos:

POST /v1/agendamentos/fixo  
POST /v1/agendamentos/variavel  
GET /v1/agendamentos/disponibilidade  


## Arquitetura

Stack atual:

- Python 3.11+
- FastAPI
- PostgreSQL
- Uvicorn
- AWS (RDS / EC2 – ambiente futuro)

Arquitetura simplificada:

Agente IA → API FastAPI → Banco PostgreSQL


## Autenticação

A API utiliza autenticação via API Key.

Header obrigatório:

Authorization: Bearer hash da Key

Caso o header não seja informado, a API retorna:

401 - Header Authorization não informado



## Licença

Projeto proprietário – AiGENTEGOV.  
Uso restrito a ambientes autorizados.
