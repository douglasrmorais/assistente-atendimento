"""Dados do negócio fictício atendido pelo bot.

Para trocar de negócio (clínica, IFPB, etc.), edite apenas este arquivo
e as intenções em bot.py.
"""

NEGOCIO = {
    "nome": "Pizzaria Bella Massa",
    "horario": "terça a domingo, das 18h às 23h30 (fechado às segundas)",
    "endereco": "Rua das Flores, 123 - Centro",
    "telefone": "(00) 90000-0000",
    "taxa_entrega": 6.00,
    "entrega_gratis_acima_de": 80.00,
    "tempo_entrega": "40 a 60 minutos",
    "pagamentos": ["Pix", "cartão de crédito", "cartão de débito", "dinheiro"],
}

# "palavras" são os termos (sem acento) que o cliente pode usar para citar a pizza.
CARDAPIO = [
    {
        "nome": "Margherita",
        "ingredientes": "molho de tomate, mussarela, tomate fatiado e manjericão",
        "preco": 42.00,
        "palavras": ["margherita", "marguerita"],
    },
    {
        "nome": "Calabresa",
        "ingredientes": "mussarela, calabresa fatiada e cebola",
        "preco": 40.00,
        "palavras": ["calabresa"],
    },
    {
        "nome": "Frango com Catupiry",
        "ingredientes": "frango desfiado, catupiry e milho",
        "preco": 46.00,
        "palavras": ["frango", "catupiry"],
    },
    {
        "nome": "Quatro Queijos",
        "ingredientes": "mussarela, provolone, parmesão e gorgonzola",
        "preco": 48.00,
        "palavras": ["quatro queijos", "4 queijos"],
    },
    {
        "nome": "Portuguesa",
        "ingredientes": "presunto, ovos, cebola, ervilha e mussarela",
        "preco": 47.00,
        "palavras": ["portuguesa"],
    },
    {
        "nome": "Chocolate com Morango",
        "ingredientes": "chocolate ao leite e morangos (doce)",
        "preco": 44.00,
        "palavras": ["chocolate", "morango"],
    },
]


def moeda(valor: float) -> str:
    """Formata 42.0 como 'R$ 42,00'."""
    return f"R$ {valor:.2f}".replace(".", ",")


def descricao_para_llm() -> str:
    """Texto com os dados do negócio, usado no prompt do LLM."""
    linhas_cardapio = "\n".join(
        f"- {p['nome']}: {p['ingredientes']} - {moeda(p['preco'])}" for p in CARDAPIO
    )
    return (
        f"Nome: {NEGOCIO['nome']}\n"
        f"Horário: {NEGOCIO['horario']}\n"
        f"Endereço: {NEGOCIO['endereco']}\n"
        f"Telefone: {NEGOCIO['telefone']}\n"
        f"Entrega: taxa de {moeda(NEGOCIO['taxa_entrega'])}, grátis acima de "
        f"{moeda(NEGOCIO['entrega_gratis_acima_de'])}; tempo médio de {NEGOCIO['tempo_entrega']}\n"
        f"Pagamento: {', '.join(NEGOCIO['pagamentos'])}\n"
        f"Cardápio:\n{linhas_cardapio}"
    )
