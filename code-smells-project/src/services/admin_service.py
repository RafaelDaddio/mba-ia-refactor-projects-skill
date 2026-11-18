"""Operações administrativas: reset do banco e execução de SQL."""
import logging

from src.models.admin_model import ConsultaInvalida
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, admin, permitir_sql):
        self.admin = admin
        self.permitir_sql = permitir_sql

    def resetar_banco(self):
        with self.admin.transacao():
            self.admin.limpar_dados()
        logger.warning("Banco de dados resetado")

    def exigir_sql_habilitado(self):
        """A execução de SQL recebido fica desligada até ser habilitada na configuração."""
        if not self.permitir_sql:
            raise AppError("Endpoint desabilitado", status=403)

    def executar_sql(self, sql):
        """Devolve as linhas de um SELECT, ou None para os demais comandos."""
        self.exigir_sql_habilitado()
        eh_consulta = sql.strip().upper().startswith("SELECT")
        try:
            if eh_consulta:
                return self.admin.consultar(sql)
            with self.admin.transacao():
                self.admin.executar(sql)
        except ConsultaInvalida as erro:
            raise AppError("Erro ao executar a query: " + str(erro), status=400) from erro
        logger.warning("Comando SQL administrativo executado")
        return None
