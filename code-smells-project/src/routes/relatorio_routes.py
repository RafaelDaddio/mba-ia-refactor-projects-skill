"""Rotas de relatórios (dados de todas as contas: administrador)."""
from flask import Blueprint

from src.middlewares.auth import somente_admin


def criar_blueprint(controller):
    bp = Blueprint("relatorios", __name__)
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", somente_admin(controller.vendas), methods=["GET"])
    return bp
