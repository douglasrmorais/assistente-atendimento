import pytest

from app.bot import normalizar, responder_por_regras
from app.llm import _montar_mensagens


def test_normalizar_remove_acentos_e_pontuacao():
    assert normalizar("  Horário?! ") == " horario "


@pytest.mark.parametrize(
    "pergunta, trecho_esperado",
    [
        ("Qual o horário?", "terça a domingo"),
        ("Que horas vocês abrem?", "terça a domingo"),
        ("Me manda o cardápio", "Margherita"),
        ("Onde fica a pizzaria?", "Rua das Flores"),
        ("Aceitam cartão?", "Pix"),
        ("Tem pizza de 4 queijos?", "Quatro Queijos"),
        ("Bom dia", "Bem-vindo"),
        ("Valeu!", "Bom apetite"),
    ],
)
def test_regras_reconhecem_intencoes(pergunta, trecho_esperado):
    assert trecho_esperado in responder_por_regras(pergunta)


def test_palavra_inteira_nao_confunde_trechos():
    # 'oi' aparece dentro de 'comoida', mas não deve ser tratado como saudação
    assert responder_por_regras("xoixo") is None


def test_pergunta_fora_do_escopo_devolve_none():
    assert responder_por_regras("Qual a capital da França?") is None


def test_montar_mensagens_alterna_papeis_e_comeca_com_user():
    historico = [
        {"remetente": "bot", "texto": "resposta antiga"},
        {"remetente": "cliente", "texto": "oi"},
        {"remetente": "cliente", "texto": "tudo bem?"},
        {"remetente": "bot", "texto": "tudo!"},
        {"remetente": "cliente", "texto": "qual o preço?"},
    ]
    assert _montar_mensagens(historico) == [
        {"role": "user", "content": "oi\ntudo bem?"},
        {"role": "assistant", "content": "tudo!"},
        {"role": "user", "content": "qual o preço?"},
    ]
