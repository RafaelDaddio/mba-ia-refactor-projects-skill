import logging

from src.models.admin_model import SqlInvalido
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, admin):
        self.admin = admin

    def resetar_banco(self):
        self.admin.resetar()
        logger.warning("Banco de dados resetado por requisição administrativa")

    def executar_sql(self, sql):
        try:
            linhas = self.admin.executar_sql(sql)
        except SqlInvalido as erro:
            raise AppError(f"Erro ao executar a query: {erro}") from None
        logger.warning("SQL administrativo executado")
        return linhas
