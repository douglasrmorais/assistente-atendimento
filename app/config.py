"""Configurações do projeto, lidas de variáveis de ambiente (arquivo .env).

As funções leem o ambiente na hora da chamada (e não na importação) para
facilitar os testes, que trocam o banco e a chave temporariamente.
"""
import os

from dotenv import load_dotenv

# Carrega o arquivo .env (se existir). Variáveis já definidas no sistema têm prioridade.
load_dotenv()

_PLACEHOLDERS = {"", "cole_sua_chave_aqui", "sua_chave_aqui"}


def db_path() -> str:
    return os.getenv("DB_PATH", "atendimento.db")


def anthropic_api_key() -> str:
    """Devolve a chave da API ou string vazia se não estiver configurada."""
    chave = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return "" if chave in _PLACEHOLDERS else chave


def anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
