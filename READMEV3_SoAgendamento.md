# AiGENTEGOV – API de Agendamento e Notificações

API responsável pelo gerenciamento de agendamentos fixos e variáveis, bem como pela consulta e atualização de dados relacionados a notificações de agendamento.

Esta API compõe a camada de serviços do sistema AiGENTEGOV e é consumida por:

- Agente IA (WhatsApp)
- Sistema Web administrativo
- Integrações institucionais futuras


## Objetivo

Permitir:

- Consulta de cidadão (por telefone, CPF ou identificador institucional)
- Verificação se o serviço permite agendamento automatizado via Agente IA
- Consulta de disponibilidade
- Consulta de múltiplas datas e horários disponíveis para agendamento de slot fixo
- Registro de agendamentos fixos
- Registro de agendamentos variáveis
- Atualização de status do agendamento (confirmado, cancelado, reagendado)
- Integração com sistema legado (ex.: sistema de transporte)


## Módulo de Agendamentos

API responsável pelo gerenciamento de dois tipos de agendamento:

### Agendamento Fixo

Utiliza grade horária previamente definida, com slots de atendimento configurados por serviço, profissional ou unidade.

Exemplo: atendimento clínico geral, que tem uma grade horária do serviço para cada especialista que atende determinado serviço.

### Agendamento Evento Variável

Não utiliza grade horária fixa. A solicitação de agendamento é registrada e em outro momento a confirmação de agendamento é realizada.

Exemplo: transporte ou eventos com janela flexível.


## Parametrização de Serviço

Os serviços podem estar configurados como:

- Permite agendamento automatizado via Agente IA
- Não permite agendamento automatizado

Caso o serviço não permita agendamento via IA:

- O Agente IA informa ao cidadão a indisponibilidade de autoagendamento.
- O atendimento é encaminhado para fluxo humano.
- Registro sobre a informação da solicitação é registrado.


## Fluxo Simplificado – Agendamento

### 1. Recebimento

O Agente IA recebe mensagem via WhatsApp relacionada a agendamento.

### 2. Identificação da Intenção

A mensagem é classificada como:

- Solicitação de novo agendamento
- Solicitação de informações sobre agendamento existente



### Caso 2 – Solicitação de Novo Agendamento

1. A API é consultada para identificar:
   - Parâmetro de agendamento do servico (Permite Agendamento por Agente IA ou Não Permite Agendamento por Agente IA)
   - Tipo de serviço (slot fixo ou evento variável)
   
####  Permite Agendamento por Agente IA  
   - Entra no fluxo Agendamento Fixo Permite Agendamento

   1.1 Caso o serviço não permita agendamento via IA:
      - O Agente IA informa o cidadão.
      - O atendimento é encaminhado para fluxo humano.

2. Caso o serviço permita agendamento via IA:
   - O fluxo segue conforme o tipo de agendamento.


#### Agendamento Fixo e Permite Agendamento por Agente IA

   - A API verifica agendas ativas e elegíveis.
   - A API retorna os horários disponíveis.
   - O Agente IA apresenta as opções ao cidadão.
   - O cidadão seleciona o horário desejado.
   - A API registra o agendamento.
   - O Agente IA confirma o agendamento ao cidadão.
   - O histórico é registrado automaticamente.

#### Agendamento Variável e Permite Agendamento por Agente IA
   - O Agente IA confirma a solicitação do cidadão.
   - A API registra a solicitação.
   - O Agente IA confirma a inscrição ao cidadão.


#### (Agendamento Variável e NÃO Permite Agendamento por Agente IA) e (Agendamento Fixo e NÃO Permite Agendamento por Agente IA)
   - O Agente IA informa o cidadão.
   - A API registra a solicitação como informação.
   - O atendimento é encaminhado para fluxo humano.


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
