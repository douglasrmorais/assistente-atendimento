"""Relatório simples sobre as conversas salvas no banco.

Uso:
    python relatorio.py                # usa o banco padrão (atendimento.db)
    python relatorio.py --db demo.db   # usa outro arquivo de banco
"""
import argparse
import os

from app.database import conexao, criar_tabelas

# ---------------------------------------------------------------------------
# Consultas SQL (cada uma mostra um conceito: COUNT, GROUP BY, JOIN, subconsulta)
# ---------------------------------------------------------------------------

SQL_RESUMO = """
SELECT COUNT(DISTINCT conversa_id)                                   AS conversas,
       COUNT(*)                                                      AS mensagens,
       ROUND(1.0 * COUNT(*) / NULLIF(COUNT(DISTINCT conversa_id), 0), 1) AS media_por_conversa
FROM mensagens;
"""

SQL_MENSAGENS_POR_DIA = """
SELECT DATE(criada_em)               AS dia,
       COUNT(*)                      AS mensagens,
       COUNT(DISTINCT conversa_id)   AS conversas
FROM mensagens
GROUP BY DATE(criada_em)
ORDER BY dia;
"""

SQL_PERGUNTAS_FREQUENTES = """
SELECT LOWER(TRIM(texto)) AS pergunta,
       COUNT(*)           AS vezes
FROM mensagens
WHERE remetente = 'cliente'
GROUP BY LOWER(TRIM(texto))
ORDER BY vezes DESC, pergunta
LIMIT 5;
"""

SQL_ORIGEM_DAS_RESPOSTAS = """
SELECT origem,
       COUNT(*) AS respostas,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM mensagens WHERE remetente = 'bot'), 1) AS percentual
FROM mensagens
WHERE remetente = 'bot'
GROUP BY origem
ORDER BY respostas DESC;
"""

# Auto-JOIN: liga cada resposta 'fallback' do bot à pergunta do cliente que a antecedeu.
SQL_SEM_RESPOSTA = """
SELECT LOWER(TRIM(cli.texto)) AS pergunta_sem_resposta,
       COUNT(*)               AS vezes
FROM mensagens bot
JOIN mensagens cli
  ON cli.id = (SELECT MAX(x.id)
               FROM mensagens x
               WHERE x.conversa_id = bot.conversa_id
                 AND x.remetente = 'cliente'
                 AND x.id < bot.id)
WHERE bot.remetente = 'bot' AND bot.origem = 'fallback'
GROUP BY LOWER(TRIM(cli.texto))
ORDER BY vezes DESC, pergunta_sem_resposta
LIMIT 5;
"""

SQL_CONVERSAS_MAIS_LONGAS = """
SELECT c.id        AS conversa,
       c.criada_em AS inicio,
       COUNT(m.id) AS mensagens
FROM conversas c
JOIN mensagens m ON m.conversa_id = c.id
GROUP BY c.id
ORDER BY mensagens DESC, c.id
LIMIT 5;
"""


def consultar(sql: str) -> list[dict]:
    with conexao() as conn:
        return [dict(linha) for linha in conn.execute(sql).fetchall()]


def imprimir_tabela(titulo: str, linhas: list[dict]) -> None:
    print(f"\n=== {titulo} ===")
    if not linhas:
        print("(sem dados)")
        return
    colunas = list(linhas[0].keys())
    larguras = [max(len(c), *(len(str(l[c])) for l in linhas)) for c in colunas]
    print("  ".join(c.ljust(w) for c, w in zip(colunas, larguras)))
    print("  ".join("-" * w for w in larguras))
    for linha in linhas:
        print("  ".join(str(linha[c]).ljust(w) for c, w in zip(colunas, larguras)))


def gerar_relatorio() -> None:
    criar_tabelas()  # evita erro se o relatório rodar antes da API
    imprimir_tabela("Resumo geral", consultar(SQL_RESUMO))
    imprimir_tabela("Mensagens por dia", consultar(SQL_MENSAGENS_POR_DIA))
    imprimir_tabela("Perguntas mais frequentes", consultar(SQL_PERGUNTAS_FREQUENTES))
    imprimir_tabela("Como o bot respondeu", consultar(SQL_ORIGEM_DAS_RESPOSTAS))
    imprimir_tabela("Perguntas que o bot não soube responder", consultar(SQL_SEM_RESPOSTA))
    imprimir_tabela("Conversas mais longas", consultar(SQL_CONVERSAS_MAIS_LONGAS))
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Relatório das conversas do Assistente de Atendimento.")
    parser.add_argument("--db", help="caminho do arquivo SQLite (padrão: atendimento.db)")
    args = parser.parse_args()
    if args.db:
        os.environ["DB_PATH"] = args.db
    gerar_relatorio()
