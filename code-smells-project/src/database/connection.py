"""Conexão SQLite por requisição e controle de transação."""
import sqlite3
from contextlib import contextmanager

from flask import g

_CHAVE_G = "conexao_db"


class Database:
    """Entrega uma conexão por contexto de aplicação (requisição) do Flask."""

    def __init__(self, path):
        self.path = path

    @property
    def conn(self):
        conexao = g.get(_CHAVE_G)
        if conexao is None:
            conexao = sqlite3.connect(self.path)
            conexao.row_factory = sqlite3.Row
            conexao.execute("PRAGMA foreign_keys = ON")
            setattr(g, _CHAVE_G, conexao)
        return conexao

    @contextmanager
    def transaction(self):
        """Tudo ou nada. Reentrante: só o bloco mais externo confirma ou desfaz."""
        conexao = self.conn
        if conexao.in_transaction:
            yield conexao
            return
        conexao.execute("BEGIN IMMEDIATE")
        try:
            yield conexao
        except BaseException:
            conexao.rollback()
            raise
        conexao.commit()

    def close(self, _error=None):
        conexao = g.pop(_CHAVE_G, None)
        if conexao is not None:
            conexao.close()
