"""Modelos (Pydantic) que definem e validam o que entra e sai da API."""
from pydantic import BaseModel, ConfigDict, Field


class ChatEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    mensagem: str = Field(..., min_length=1, max_length=1000, examples=["Qual o horário de vocês?"])
    conversa_id: int | None = Field(
        default=None,
        description="Omita para iniciar uma conversa nova; envie o id para continuar uma existente.",
    )


class ChatSaida(BaseModel):
    conversa_id: int
    resposta: str
    origem: str = Field(description="'regra', 'llm' ou 'fallback'")


class MensagemSaida(BaseModel):
    id: int
    remetente: str
    texto: str
    origem: str | None
    criada_em: str


class ConversaSaida(BaseModel):
    id: int
    criada_em: str
    mensagens: list[MensagemSaida]
