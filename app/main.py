"""API REST do Assistente de Atendimento (FastAPI)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app import bot, database
from app.schemas import ChatEntrada, ChatSaida, ConversaSaida


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.criar_tabelas()  # cria as tabelas na primeira execução
    yield


app = FastAPI(
    title="Assistente de Atendimento",
    description="Chatbot de atendimento com regras por palavra-chave, LLM como apoio e histórico em SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/saude", tags=["infra"])
def saude():
    """Verifica se a API está no ar."""
    return {"status": "ok"}


# Estes endpoints são 'def' (e não 'async def') de propósito: a chamada ao LLM e ao
# SQLite é bloqueante, e o FastAPI roda funções 'def' em threads, sem travar o servidor.
@app.post("/chat", response_model=ChatSaida, tags=["chat"])
def chat(entrada: ChatEntrada):
    """Recebe a mensagem do cliente e devolve a resposta do bot."""
    if entrada.conversa_id is None:
        conversa_id = database.criar_conversa()
    elif database.conversa_existe(entrada.conversa_id):
        conversa_id = entrada.conversa_id
    else:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    database.salvar_mensagem(conversa_id, "cliente", entrada.mensagem)

    historico = database.ultimas_mensagens(conversa_id, limite=10)
    resposta, origem = bot.responder(entrada.mensagem, historico)

    database.salvar_mensagem(conversa_id, "bot", resposta, origem=origem)
    return ChatSaida(conversa_id=conversa_id, resposta=resposta, origem=origem)


@app.get("/conversas/{conversa_id}", response_model=ConversaSaida, tags=["chat"])
def historico_da_conversa(conversa_id: int):
    """Devolve o histórico completo de uma conversa."""
    conversa = database.buscar_conversa(conversa_id)
    if conversa is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return conversa
