"""Simula conversas de clientes com o bot, chamando a API de verdade.

A API precisa estar rodando (uvicorn app.main:app --reload).
Depois de rodar este script, gere o relatório com: python relatorio.py

Usa só a biblioteca padrão e envia JSON em UTF-8, então acentos funcionam
em qualquer sistema (inclusive Windows).
"""
import json
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/chat"

# Cada lista é uma conversa. As perguntas repetidas e as que o bot não sabe
# ("opção vegana", "sem cebola") deixam o relatório mais interessante.
CONVERSAS = [
    [
        "Oi",
        "Qual o horário de funcionamento?",
        "Quero ver o cardápio",
        "Quanto custa a calabresa?",
        "Vocês entregam?",
        "Aceitam pix?",
        "Tem opção vegana?",
        "Obrigado",
    ],
    [
        "Bom dia",
        "Qual o horário de funcionamento?",
        "Tem opção vegana?",
        "Posso pedir sem cebola?",
        "Qual o endereço?",
    ],
    [
        "Qual o horário de funcionamento?",
        "Aceitam cartão?",
        "Falar com atendente",
        "Tchau",
    ],
]


def enviar(mensagem: str, conversa_id: int | None = None) -> dict:
    corpo = {"mensagem": mensagem}
    if conversa_id is not None:
        corpo["conversa_id"] = conversa_id
    requisicao = urllib.request.Request(
        URL,
        data=json.dumps(corpo).encode("utf-8"),  # ensure_ascii=True: acentos viram \uXXXX
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        return json.load(resposta)


def main() -> None:
    total = 0
    for numero, mensagens in enumerate(CONVERSAS, start=1):
        print(f"\n--- Conversa {numero} ---")
        conversa_id = None  # a primeira mensagem abre uma conversa nova
        for texto in mensagens:
            dados = enviar(texto, conversa_id)
            conversa_id = dados["conversa_id"]  # as próximas continuam a mesma conversa
            print(f"[{dados['origem']:8}] {texto}")
            total += 1
    print(f"\nPronto: {total} perguntas enviadas. Agora rode: python relatorio.py")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError:
        print("Não consegui conectar na API. Ela está rodando? (uvicorn app.main:app --reload)")