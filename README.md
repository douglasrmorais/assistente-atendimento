# Assistente de Atendimento

Chatbot de atendimento para uma pizzaria fictícia, feito em Python com uma API REST (FastAPI).
Ele responde dúvidas comuns (horário, cardápio, preço, entrega, pagamento) por regras de palavra-chave e, quando não sabe, consulta um LLM (Claude).
Todas as conversas ficam salvas em SQLite, e um script SQL gera um relatório de uso.

**Tecnologias:** Python 3.10+ · FastAPI · SQLite · API da Anthropic (Claude) · pytest · Git/GitHub

## Como rodar

```bash
# 1. Clone e entre na pasta
git clone https://github.com/douglasrmorais/assistente-atendimento.git
cd assistente-atendimento

# 2. Crie o ambiente virtual e instale as dependências
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Opcional) Ative o LLM: copie o .env de exemplo e cole sua chave
cp .env.example .env               # Windows: copy .env.example .env
# edite o .env e preencha ANTHROPIC_API_KEY=...

# 4. Suba a API
uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000/docs** para testar os endpoints pelo navegador (Swagger).
Sem chave de API o projeto funciona normalmente: perguntas fora das regras recebem uma resposta padrão (fallback).

### Testes

```bash
pip install -r requirements-dev.txt
pytest
```

### Relatório

```bash
python relatorio.py                 # usa o banco real (atendimento.db)

# ou, para ver com dados de exemplo:
python popular_demo.py
python relatorio.py --db demo.db
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/chat` | Recebe a mensagem e devolve a resposta do bot |
| GET | `/conversas/{id}` | Devolve o histórico de uma conversa |
| GET | `/saude` | Verifica se a API está no ar |

## Exemplo de uso

**Requisição** (inicia uma conversa nova):

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Qual o horário de funcionamento?"}'
```

**Resposta:**

```json
{
  "conversa_id": 1,
  "resposta": "Funcionamos terça a domingo, das 18h às 23h30 (fechado às segundas).",
  "origem": "regra"
}
```

Para continuar a mesma conversa, envie o `conversa_id`:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Quanto custa a calabresa?", "conversa_id": 1}'
```

```json
{
  "conversa_id": 1,
  "resposta": "Calabresa: mussarela, calabresa fatiada e cebola. Preço: R$ 40,00.",
  "origem": "regra"
}
```

O campo `origem` mostra quem respondeu: `regra`, `llm` ou `fallback`.

Exemplo de saída do `relatorio.py`:

```
=== Como o bot respondeu ===
origem    respostas  percentual
--------  ---------  ----------
regra     21         87.5
fallback  3          12.5

=== Perguntas que o bot não soube responder ===
pergunta_sem_resposta    vezes
-----------------------  -----
tem opção vegana?        2
posso pedir sem cebola?  1
```

## Como funciona

```
Cliente ──POST /chat──> FastAPI ──> salva mensagem (SQLite)
                                      │
                                      ▼
                            1. Regras por palavra-chave ──achou──> resposta (origem: regra)
                                      │ não achou
                                      ▼
                            2. LLM (Claude), com o histórico ──ok──> resposta (origem: llm)
                                      │ sem chave ou erro
                                      ▼
                            3. Mensagem padrão ───────────────────> resposta (origem: fallback)
                                      │
                                      ▼
                            salva resposta (SQLite) ──> devolve JSON
```

**Banco de dados:** duas tabelas, `conversas` (id, criada_em) e `mensagens` (id, conversa_id, remetente, texto, origem, criada_em), ligadas por chave estrangeira.

**Estrutura de pastas:**

```
app/
  main.py       # rotas da API
  bot.py        # regras + decisão regra/LLM/fallback
  llm.py        # chamada à API da Anthropic
  database.py   # SQL e conexão com o SQLite
  schemas.py    # validação de entrada e saída (Pydantic)
  negocio.py    # dados da pizzaria (cardápio, horário...)
  config.py     # variáveis de ambiente
tests/          # testes automatizados (pytest)
relatorio.py    # consultas SQL (COUNT, GROUP BY, JOIN)
popular_demo.py # dados de exemplo para o relatório
```

## Decisões de projeto

- **Regras primeiro, LLM depois.** Perguntas comuns são respondidas por regras: é instantâneo, não custa nada e a resposta é previsível (o LLM poderia errar um preço). O LLM só entra no que as regras não cobrem.
- **Fallback.** Se a chave não estiver configurada ou a chamada falhar (rede, limite de uso), o bot responde com uma mensagem padrão. O LLM é um reforço, e a API não depende dele para funcionar. Testei esse caminho com uma chave inválida.
- **SQLite.** Não exige instalação, o banco é um arquivo e atende bem a este volume. O custo é a concorrência limitada de escrita.
- **`sqlite3` puro, sem ORM.** Deixa o SQL visível e fácil de explicar.
- **Consultas parametrizadas (`?`)** em todo o código, para evitar SQL injection.
- **Rotas `def` e não `async def`.** A chamada ao LLM e ao SQLite é bloqueante; com `def`, o FastAPI usa threads e não trava o servidor.
- **Prompt do LLM restrito** aos dados do negócio, com a instrução de não inventar preços nem itens.
- **Chave de API em `.env`**, fora do Git (`.gitignore`).

## O que aprendi

- **Organização de uma API REST em camadas.** Separei rotas, lógica do bot, acesso ao banco e integração com o LLM em arquivos diferentes, o que facilita testar cada parte sozinha. Usei o FastAPI com validação de entrada pelo Pydantic e vi na prática as respostas 200, 404 e 422.
- **SQL na prática.** Modelei duas tabelas ligadas por chave estrangeira e escrevi consultas com `COUNT`, `GROUP BY`, `JOIN` e uma subconsulta (um auto-JOIN que liga cada resposta "fallback" à pergunta que a causou). Todas as consultas são parametrizadas, para evitar SQL injection.
- **Tratar o LLM como uma dependência que pode falhar.** O bot responde por regras e só chama o LLM quando precisa. Se a chave não existe ou a chamada falha, ele cai no fallback e a API continua funcionando (esse comportamento foi validado com uma chave inválida, que gerou erro 401 sem derrubar o bot).
- **Testes automatizados.** O projeto tem 27 testes com pytest, que usam um banco temporário e substituem o LLM por uma resposta fixa, para testar sem gastar chamadas à API.
- **Um bug que encontrei.** Ao testar pelo Swagger (`/docs`), o campo `conversa_id` vem preenchido com `0` e a API respondia 404. Resolvi tratando `0` como "conversa nova". Aprendi que testar pela interface revela casos que os testes automatizados não cobriram.
- **Ambiente de desenvolvimento.** Usei ambiente virtual (venv), dependências em `requirements.txt` e a chave da API em um arquivo `.env` fora do Git.
- **Trabalhar com IA como apoio.** Desenvolvi o projeto com o apoio do Claude. Meu papel foi executar, testar, depurar e entender o código, em vez de aceitá-lo sem revisar.

## O que eu melhoraria

- Trocar a correspondência por palavra-chave por classificação de intenção (embeddings ou o próprio LLM).
- Usar o relatório de "perguntas sem resposta" para criar novas regras.
- Autenticação e limite de requisições (rate limiting) na API.
- Migrar para PostgreSQL e usar migrações (Alembic).
- Integrar com Telegram ou WhatsApp.
- Rodar em Docker e configurar CI com GitHub Actions para executar os testes a cada push.
