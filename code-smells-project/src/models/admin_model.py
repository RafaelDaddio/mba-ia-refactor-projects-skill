import sqlite3

# Ordem que respeita as referências entre as tabelas.
TABELAS_PARA_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class SqlInvalido(Exception):
    """O banco recusou o SQL recebido."""


class AdminModel:
    def __init__(self, conexao):
        self._conexao = conexao

    def resetar(self):
        conexao = self._conexao()
        with conexao:
            for tabela in TABELAS_PARA_RESET:
                conexao.execute(f"DELETE FROM {tabela}")

    def executar_sql(self, sql):
        """Executa o SQL recebido. SELECT devolve as linhas; o resto é gravado e devolve None."""
        conexao = self._conexao()
        try:
            if sql.strip().upper().startswith("SELECT"):
                return [dict(row) for row in conexao.execute(sql).fetchall()]
            with conexao:
                conexao.execute(sql)
            return None
        except sqlite3.Error as erro:
            raise SqlInvalido(str(erro)) from erro
