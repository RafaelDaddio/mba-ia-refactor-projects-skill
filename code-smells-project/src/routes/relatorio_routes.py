"""Rotas de relatórios: reúnem dados de todas as contas, só para o administrador."""
from flask import Blueprint


def criar_blueprint(controller, auth):
    bp = Blueprint("relatorios", __name__)
    bp.add_url_rule("/relatorios/vendas", view_func=auth.admin_only(controller.vendas), methods=["GET"])
    return bp
