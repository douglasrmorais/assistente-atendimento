import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com banco temporário e sem chave de LLM."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "teste.db"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    from app.main import app

    with TestClient(app) as c:  # 'with' dispara o lifespan (cria as tabelas)
        yield c


def test_saude(client):
    assert client.get("/saude").json() == {"status": "ok"}


def test_chat_responde_por_regra_e_cria_conversa(client):
    r = client.post("/chat", json={"mensagem": "Qual o horário de funcionamento?"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["origem"] == "regra"
    assert "18h" in dados["resposta"]
    assert dados["conversa_id"] == 1


def test_pizza_especifica_devolve_preco(client):
    dados = client.post("/chat", json={"mensagem": "Quanto custa a calabresa?"}).json()
    assert dados["origem"] == "regra"
    assert "R$ 40,00" in dados["resposta"]


def test_saudacao_nao_rouba_pergunta_especifica(client):
    dados = client.post("/chat", json={"mensagem": "Oi, vocês entregam?"}).json()
    assert "taxa" in dados["resposta"].lower()


def test_pergunta_desconhecida_sem_chave_usa_fallback(client):
    dados = client.post("/chat", json={"mensagem": "Tem opção vegana?"}).json()
    assert dados["origem"] == "fallback"
    assert "atendente" in dados["resposta"]


def test_pergunta_desconhecida_com_llm(client, monkeypatch):
    monkeypatch.setattr("app.bot.perguntar_llm", lambda historico: "Resposta do LLM")
    dados = client.post("/chat", json={"mensagem": "Tem opção vegana?"}).json()
    assert dados == {"conversa_id": 1, "resposta": "Resposta do LLM", "origem": "llm"}


def test_historico_guarda_mensagens_em_ordem(client):
    primeira = client.post("/chat", json={"mensagem": "Oi"}).json()
    cid = primeira["conversa_id"]
    client.post("/chat", json={"mensagem": "Aceitam pix?", "conversa_id": cid})

    r = client.get(f"/conversas/{cid}")
    assert r.status_code == 200
    mensagens = r.json()["mensagens"]
    assert [m["remetente"] for m in mensagens] == ["cliente", "bot", "cliente", "bot"]
    assert mensagens[2]["texto"] == "Aceitam pix?"


def test_conversa_inexistente_retorna_404(client):
    assert client.get("/conversas/999").status_code == 404
    r = client.post("/chat", json={"mensagem": "Oi", "conversa_id": 999})
    assert r.status_code == 404


def test_mensagem_vazia_retorna_422(client):
    assert client.post("/chat", json={"mensagem": "   "}).status_code == 422
