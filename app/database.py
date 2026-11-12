"""Acesso ao banco SQLite.

Usei o módulo sqlite3 da biblioteca padrão (sem ORM) de propósito:
assim o SQL fica explícito e fácil de explicar numa entrevista.
Todas as consultas usam parâmetros (?) para evitar SQL injection.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    criada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mensagens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id INTEGER NOT NULL,
    remetente   TEXT NOT NULL CHECK (remetente IN ('cliente', 'bot')),
    texto       TEXT NOT NULL,
    origem      TEXT CHECK (origem IN ('regra', 'llm', 'fallback')),
    criada_em   TEXT NOT NULL,
    FOREIGN KEY (conversa_id) REFERENCES conversas (id)
);

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens (conversa_id);
"""


def agora() -> str:
    """Data/hora atual em UTC, formato ISO 8601 (ex.: 2026-11-09T14:30:00+00:00)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def conexao():
    """Abre a conexão, faz commit no sucesso, rollback no erro e sempre fecha."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def criar_tabelas() -> None:
    with conexao() as conn:
        conn.executescript(SCHEMA)


def criar_conversa(criada_em: str | None = None) -> int:
    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO conversas (criada_em) VALUES (?)", (criada_em or agora(),)
        )
        return cur.lastrowid


def conversa_existe(conversa_id: int) -> bool:
    with conexao() as conn:
        linha = conn.execute(
            "SELECT 1 FROM conversas WHERE id = ?", (conversa_id,)
        ).fetchone()
        return linha is not None


def salvar_mensagem(
    conversa_id: int,
    remetente: str,
    texto: str,
    origem: str | None = None,
    criada_em: str | None = None,
) -> int:
    with conexao() as conn:
        cur = conn.execute(
            "INSERT INTO mensagens (conversa_id, remetente, texto, origem, criada_em) "
            "VALUES (?, ?, ?, ?, ?)",
            (conversa_id, remetente, texto, origem, criada_em or agora()),
        )
        return cur.lastrowid


def buscar_conversa(conversa_id: int) -> dict | None:
    """Devolve a conversa com todas as mensagens em ordem, ou None se não existir."""
    with conexao() as conn:
        conversa = conn.execute(
            "SELECT id, criada_em FROM conversas WHERE id = ?", (conversa_id,)
        ).fetchone()
        if conversa is None:
            return None
        mensagens = conn.execute(
            "SELECT id, remetente, texto, origem, criada_em "
            "FROM mensagens WHERE conversa_id = ? ORDER BY id",
            (conversa_id,),
        ).fetchall()
        return {**dict(conversa), "mensagens": [dict(m) for m in mensagens]}


def ultimas_mensagens(conversa_id: int, limite: int = 10) -> list[dict]:
    """Últimas N mensagens da conversa, da mais antiga para a mais nova."""
    with conexao() as conn:
        linhas = conn.execute(
            "SELECT remetente, texto FROM ("
            "  SELECT id, remetente, texto FROM mensagens "
            "  WHERE conversa_id = ? ORDER BY id DESC LIMIT ?"
            ") ORDER BY id ASC",
            (conversa_id, limite),
        ).fetchall()
        return [dict(l) for l in linhas]
