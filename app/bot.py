"""Lógica do bot: regras por palavra-chave primeiro, LLM depois, fallback por último.

Ordem de decisão em responder():
  1. regra  -> a pergunta bate com uma intenção conhecida (rápido, grátis, previsível)
  2. llm    -> não bateu com nada; pergunta ao modelo de linguagem
  3. fallback -> sem chave ou LLM com erro; mensagem padrão
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

from app.llm import perguntar_llm
from app.negocio import CARDAPIO, NEGOCIO, moeda

MENSAGEM_FALLBACK = (
    "Desculpe, não consegui entender sua pergunta. "
    f"Fale com um atendente pelo telefone {NEGOCIO['telefone']}."
)


def normalizar(texto: str) -> str:
    """minúsculas, sem acentos e sem pontuação: 'Horário?' -> 'horario'."""
    sem_acento = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    so_letras = re.sub(r"[^a-z0-9]+", " ", sem_acento.lower())
    return f" {so_letras.strip()} "  # espaços nas pontas facilitam achar palavras inteiras


def _contem(texto_normalizado: str, termo: str) -> bool:
    """True se o termo aparece como palavra (ou frase) inteira."""
    return f" {termo} " in texto_normalizado


# ---------- Respostas ----------

def _resp_saudacao() -> str:
    return (
        f"Olá! Bem-vindo à {NEGOCIO['nome']} 🍕 "
        "Posso ajudar com cardápio, preços, horário, entrega e formas de pagamento."
    )


def _resp_horario() -> str:
    return f"Funcionamos {NEGOCIO['horario']}."


def _resp_cardapio() -> str:
    itens = "\n".join(f"• {p['nome']} - {moeda(p['preco'])}" for p in CARDAPIO)
    return f"Nosso cardápio de pizzas:\n{itens}"


def _resp_preco() -> str:
    precos = [p["preco"] for p in CARDAPIO]
    return (
        f"Nossas pizzas custam de {moeda(min(precos))} a {moeda(max(precos))}. "
        "Pergunte por um sabor específico ou peça o cardápio completo."
    )


def _resp_endereco() -> str:
    return f"Estamos na {NEGOCIO['endereco']}."


def _resp_entrega() -> str:
    return (
        f"Entregamos em {NEGOCIO['tempo_entrega']}. "
        f"A taxa é {moeda(NEGOCIO['taxa_entrega'])}, grátis em pedidos acima de "
        f"{moeda(NEGOCIO['entrega_gratis_acima_de'])}."
    )


def _resp_pagamento() -> str:
    return f"Aceitamos: {', '.join(NEGOCIO['pagamentos'])}."


def _resp_contato() -> str:
    return f"Você pode falar com a gente pelo telefone {NEGOCIO['telefone']}."


def _resp_despedida() -> str:
    return "Por nada! Qualquer dúvida, é só chamar. Bom apetite! 🍕"


@dataclass(frozen=True)
class Intencao:
    nome: str
    palavras: tuple[str, ...]
    resposta: Callable[[], str]


# A ordem importa: em caso de empate, vence a primeira.
# Saudação e despedida ficam no fim para não "roubar" perguntas como "oi, qual o horário?".
INTENCOES = [
    Intencao("horario", ("horario", "horarios", "abre", "abrem", "fecha", "fecham",
                         "funcionamento", "funciona", "aberto", "aberta", "que horas"), _resp_horario),
    Intencao("cardapio", ("cardapio", "menu", "sabores", "sabor", "opcoes", "pizzas"), _resp_cardapio),
    Intencao("preco", ("preco", "precos", "valor", "valores", "custa", "quanto custa",
                       "quanto e", "quanto sai"), _resp_preco),
    Intencao("endereco", ("endereco", "onde fica", "localizacao", "como chegar", "onde voces ficam"), _resp_endereco),
    Intencao("entrega", ("entrega", "entregam", "entregar", "delivery", "taxa", "frete"), _resp_entrega),
    Intencao("pagamento", ("pagamento", "pagar", "pix", "cartao", "credito", "debito",
                           "dinheiro", "aceitam"), _resp_pagamento),
    Intencao("contato", ("telefone", "contato", "whatsapp", "ligar", "atendente", "humano"), _resp_contato),
    Intencao("despedida", ("tchau", "obrigado", "obrigada", "brigado", "valeu", "ate mais", "ate logo"), _resp_despedida),
    Intencao("saudacao", ("oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "opa"), _resp_saudacao),
]


def _pizzas_mencionadas(texto_normalizado: str) -> list[dict]:
    return [
        p for p in CARDAPIO
        if any(_contem(texto_normalizado, normalizar(w).strip()) for w in p["palavras"])
    ]


def responder_por_regras(mensagem: str) -> str | None:
    """Devolve a resposta por regras, ou None se nenhuma regra servir."""
    texto = normalizar(mensagem)

    # 1) Cliente citou um sabor específico: responde com ingredientes e preço.
    pizzas = _pizzas_mencionadas(texto)
    if pizzas:
        return "\n".join(
            f"{p['nome']}: {p['ingredientes']}. Preço: {moeda(p['preco'])}." for p in pizzas
        )

    # 2) Pontua cada intenção pelo número de palavras-chave encontradas.
    melhor, melhor_pontos = None, 0
    for intencao in INTENCOES:
        pontos = sum(1 for palavra in intencao.palavras if _contem(texto, palavra))
        if pontos > melhor_pontos:  # ">" (e não ">=") mantém a prioridade da lista no empate
            melhor, melhor_pontos = intencao, pontos

    return melhor.resposta() if melhor else None


def responder(mensagem: str, historico: list[dict]) -> tuple[str, str]:
    """Devolve (resposta, origem). origem é 'regra', 'llm' ou 'fallback'."""
    resposta = responder_por_regras(mensagem)
    if resposta:
        return resposta, "regra"

    resposta = perguntar_llm(historico)
    if resposta:
        return resposta, "llm"

    return MENSAGEM_FALLBACK, "fallback"
