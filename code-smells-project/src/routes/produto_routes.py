"""Rotas de produtos. Leituras do catálogo são públicas; escritas exigem conta autenticada."""
from flask import Blueprint


def criar_blueprint(controller, auth):
    bp = Blueprint("produtos", __name__)
    bp.add_url_rule("/produtos", view_func=controller.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", view_func=controller.buscar, methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=controller.buscar_por_id, methods=["GET"])
    bp.add_url_rule("/produtos", view_func=auth.user_only(controller.criar), methods=["POST"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=auth.user_only(controller.atualizar), methods=["PUT"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=auth.user_only(controller.deletar), methods=["DELETE"])
    return bp
