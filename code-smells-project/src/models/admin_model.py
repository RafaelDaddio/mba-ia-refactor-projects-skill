"""Operações administrativas sobre o banco inteiro."""
import sqlite3

from src.models.base_model import BaseModel

# Ordem de exclusão: primeiro as tabelas que referenciam as outras.
_TABELAS = ("itens_pedido", "pedidos", "produtos", "usuarios")


class ConsultaInvalida(Exception):
    """O SQL recebido não pôde ser executado."""


class AdminModel(BaseModel):
    def limpar_dados(self):
        for tabela in _TABELAS:  # nomes fixos, definidos acima
            self._conn.execute(f"DELETE FROM {tabela}")

    def consultar(self, sql):
        """Executa um SELECT recebido do administrador e devolve as linhas."""
        return [dict(linha) for linha in self._executar(sql).fetchall()]

    def executar(self, sql):
        """Executa um comando SQL recebido do administrador."""
        self._executar(sql)

    def _executar(self, sql):
        try:
            return self._conn.execute(sql)
        except (sqlite3.Error, sqlite3.Warning) as erro:
            raise ConsultaInvalida(str(erro)) from erro
