"""Rotas de usuários e login. Cadastro e login são públicos."""
from flask import Blueprint

from src.middlewares.auth import somente_admin, somente_dono


def criar_blueprint(controller):
    bp = Blueprint("usuarios", __name__)
    # lista todas as contas: administrador
    bp.add_url_rule("/usuarios", "listar_usuarios", somente_admin(controller.listar), methods=["GET"])
    # dados de uma conta: dono ou administrador
    bp.add_url_rule(
        "/usuarios/<int:usuario_id>",
        "buscar_usuario",
        somente_dono("usuario_id")(controller.buscar_por_id),
        methods=["GET"],
    )
    bp.add_url_rule("/usuarios", "criar_usuario", controller.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
    return bp
