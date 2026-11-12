import pytest

import relatorio
from app import bot, database


@pytest.fixture()
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "relatorio.db"))
    database.criar_tabelas()

    # conversa 1 (dia 09): uma regra e um fallback
    c1 = database.criar_conversa("2026-11-09T10:00:00+00:00")
    for texto, origem in [("Horário?", "regra"), ("Tem vegana?", "fallback")]:
        database.salvar_mensagem(c1, "cliente", texto, criada_em="2026-11-09T10:01:00+00:00")
        database.salvar_mensagem(c1, "bot", "resp", origem=origem, criada_em="2026-11-09T10:01:00+00:00")

    # conversa 2 (dia 10): mesma pergunta de horário
    c2 = database.criar_conversa("2026-11-10T09:00:00+00:00")
    database.salvar_mensagem(c2, "cliente", "horário?", criada_em="2026-11-10T09:01:00+00:00")
    database.salvar_mensagem(c2, "bot", "resp", origem="regra", criada_em="2026-11-10T09:01:00+00:00")


def test_resumo(banco):
    resumo = relatorio.consultar(relatorio.SQL_RESUMO)[0]
    assert resumo["conversas"] == 2
    assert resumo["mensagens"] == 6
    assert resumo["media_por_conversa"] == 3.0


def test_mensagens_por_dia(banco):
    dias = relatorio.consultar(relatorio.SQL_MENSAGENS_POR_DIA)
    assert dias == [
        {"dia": "2026-11-09", "mensagens": 4, "conversas": 1},
        {"dia": "2026-11-10", "mensagens": 2, "conversas": 1},
    ]


def test_pergunta_mais_frequente_ignora_maiusculas(banco):
    top = relatorio.consultar(relatorio.SQL_PERGUNTAS_FREQUENTES)[0]
    assert top == {"pergunta": "horário?", "vezes": 2}


def test_origem_das_respostas(banco):
    origens = {l["origem"]: l["respostas"] for l in relatorio.consultar(relatorio.SQL_ORIGEM_DAS_RESPOSTAS)}
    assert origens == {"regra": 2, "fallback": 1}


def test_pergunta_sem_resposta_liga_fallback_a_pergunta_do_cliente(banco):
    linhas = relatorio.consultar(relatorio.SQL_SEM_RESPOSTA)
    assert linhas == [{"pergunta_sem_resposta": "tem vegana?", "vezes": 1}]


def test_conversas_mais_longas(banco):
    linhas = relatorio.consultar(relatorio.SQL_CONVERSAS_MAIS_LONGAS)
    assert (linhas[0]["conversa"], linhas[0]["mensagens"]) == (1, 4)
