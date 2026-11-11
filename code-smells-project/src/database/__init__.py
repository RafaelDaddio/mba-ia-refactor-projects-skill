"""Conexão SQLite por requisição e inicialização explícita do banco."""
import sqlite3

from flask import current_app, g

from src.database.schema import criar_schema
from src.database.seed import popular_se_vazio


def abrir_conexao(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def get_db():
    """Conexão do contexto atual; aberta na primeira chamada e fechada no teardown."""
    if "db" not in g:
        g.db = abrir_conexao(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def init_db(app, seed=True, senha_admin=None):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conexao = get_db()
        criar_schema(conexao)
        if seed:
            popular_se_vazio(conexao, senha_admin=senha_admin)
