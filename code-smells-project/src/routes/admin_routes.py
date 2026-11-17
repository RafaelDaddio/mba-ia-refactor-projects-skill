"""Rotas administrativas: sempre exigem credencial de administrador."""
from flask import Blueprint


def criar_blueprint(controller, auth):
    bp = Blueprint("admin", __name__)
    bp.add_url_rule("/admin/reset-db", view_func=auth.admin_only(controller.reset_database), methods=["POST"])
    bp.add_url_rule("/admin/query", view_func=auth.admin_only(controller.executar_query), methods=["POST"])
    return bp
