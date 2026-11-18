"""Consultas de diagnóstico do sistema."""
from src.models.base_model import BaseModel


class SistemaModel(BaseModel):
    def contagens(self):
        linha = self._conn.execute(
            "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
            "(SELECT COUNT(*) FROM usuarios) AS usuarios, "
            "(SELECT COUNT(*) FROM pedidos) AS pedidos"
        ).fetchone()
        return dict(linha)
