"""Rotas de usuários e login. Cadastro e login são públicos; a listagem é do administrador."""
from flask import Blueprint


def criar_blueprint(controller, auth):
    bp = Blueprint("usuarios", __name__)
    bp.add_url_rule("/usuarios", view_func=auth.admin_only(controller.listar), methods=["GET"])
    # dono da conta ou administrador: conferido no controller, com o id do caminho
    bp.add_url_rule("/usuarios/<int:usuario_id>", view_func=controller.buscar_por_id, methods=["GET"])
    bp.add_url_rule("/usuarios", view_func=controller.criar, methods=["POST"])
    bp.add_url_rule("/login", view_func=controller.login, methods=["POST"])
    return bp
