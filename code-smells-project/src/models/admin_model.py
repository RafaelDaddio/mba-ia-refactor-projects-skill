"""Operações administrativas sobre o banco inteiro."""
import sqlite3

# Ordem que respeita as chaves estrangeiras: filhos antes dos pais.
_TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class ErroSql(Exception):
    """O SQL informado pelo administrador foi recusado pelo banco."""


class AdminModel:
    def __init__(self, db):
        self.db = db

    def apagar_tudo(self):
        with self.db.transaction() as conn:
            for tabela in _TABELAS_RESET:
                conn.execute(f"DELETE FROM {tabela}")

    def consultar(self, sql):
        try:
            rows = self.db.conn.execute(sql).fetchall()
        except (sqlite3.Error, sqlite3.Warning) as erro:
            raise ErroSql(str(erro)) from erro
        return [dict(row) for row in rows]

    def executar(self, sql):
        conn = self.db.conn
        try:
            conn.execute(sql)
            conn.commit()
        except (sqlite3.Error, sqlite3.Warning) as erro:
            conn.rollback()
            raise ErroSql(str(erro)) from erro
