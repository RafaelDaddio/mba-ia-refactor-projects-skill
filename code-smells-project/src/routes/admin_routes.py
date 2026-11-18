"""Rotas administrativas (administrador)."""
from flask import Blueprint

from src.middlewares.auth import somente_admin


def criar_blueprint(controller):
    bp = Blueprint("admin", __name__)
    bp.add_url_rule("/admin/reset-db", "reset_database", somente_admin(controller.reset_database), methods=["POST"])
    bp.add_url_rule("/admin/query", "executar_query", somente_admin(controller.executar_query), methods=["POST"])
    return bp
