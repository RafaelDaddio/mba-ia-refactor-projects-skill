"""Operações administrativas: reset do banco e execução de SQL."""
import logging

from src.models.admin_model import ErroSql
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, admin, sql_habilitado=False):
        self.admin = admin
        self.sql_habilitado = sql_habilitado

    def resetar_banco(self):
        self.admin.apagar_tudo()
        logger.warning("Banco de dados resetado")

    def executar_query(self, sql):
        """Devolve as linhas de um SELECT, ou None para os demais comandos."""
        if not self.sql_habilitado:
            raise AppError("Endpoint desabilitado", status=403)
        if not isinstance(sql, str) or not sql:
            raise AppError("Query não informada")

        logger.warning("Executando SQL administrativo")
        try:
            if sql.strip().upper().startswith("SELECT"):
                return self.admin.consultar(sql)
            self.admin.executar(sql)
        except ErroSql as erro:
            raise AppError("Erro ao executar a query: " + str(erro)) from erro
        return None
