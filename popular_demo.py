"""Cria um banco de demonstração (demo.db) com conversas de vários dias.

Serve para ver o relatório funcionando sem precisar conversar com o bot antes.
Não usa o LLM: perguntas fora das regras viram 'fallback'.

Uso:
    python popular_demo.py
    python relatorio.py --db demo.db
"""
import argparse
import os
from datetime import datetime, timedelta, timezone

CONVERSAS = [
    # (dias atrás, [mensagens do cliente])
    (4, ["Oi", "Qual o horário de funcionamento?", "Obrigado"]),
    (4, ["Quero ver o cardápio", "Quanto custa a calabresa?"]),
    (3, ["Boa noite", "Vocês entregam?", "Qual a taxa?", "Aceitam pix?"]),
    (3, ["Qual o horário de funcionamento?", "Tem opção vegana?"]),
    (2, ["Oi", "Cardápio", "Tem pizza de chocolate?", "Qual o endereço?", "Tchau"]),
    (2, ["Posso pedir sem cebola?"]),
    (1, ["Qual o horário de funcionamento?", "Aceitam cartão?"]),
    (1, ["Tem opção vegana?", "Falar com atendente"]),
    (0, ["Bom dia", "Quanto custa a portuguesa?", "Vocês entregam?"]),
]


def main(db: str) -> None:
    os.environ["DB_PATH"] = db  # antes de usar o banco

    from app import bot, database

    if os.path.exists(db):
        os.remove(db)  # recomeça do zero para não duplicar dados
    database.criar_tabelas()

    base = datetime.now(timezone.utc).replace(microsecond=0)
    for dias_atras, mensagens in CONVERSAS:
        momento = base - timedelta(days=dias_atras)
        conversa_id = database.criar_conversa(momento.isoformat())
        for i, texto in enumerate(mensagens):
            quando = (momento + timedelta(minutes=i)).isoformat()
            database.salvar_mensagem(conversa_id, "cliente", texto, criada_em=quando)
            resposta = bot.responder_por_regras(texto)
            origem = "regra" if resposta else "fallback"
            database.salvar_mensagem(
                conversa_id, "bot", resposta or bot.MENSAGEM_FALLBACK, origem=origem, criada_em=quando
            )
    print(f"Banco de demonstração criado em '{db}' com {len(CONVERSAS)} conversas.")
    print(f"Agora rode: python relatorio.py --db {db}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Popula um banco de demonstração.")
    parser.add_argument("--db", default="demo.db", help="arquivo do banco (padrão: demo.db)")
    main(parser.parse_args().db)
