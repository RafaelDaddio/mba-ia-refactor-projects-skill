"""Rotas de produtos. Leituras do catálogo são públicas; escritas exigem conta autenticada."""
from flask import Blueprint

from src.middlewares.auth import somente_autenticado


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__)
    bp.add_url_rule("/produtos", "listar_produtos", controller.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", "buscar_produtos", controller.buscar, methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", controller.buscar_por_id, methods=["GET"])
    bp.add_url_rule("/produtos", "criar_produto", somente_autenticado(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "/produtos/<int:produto_id>", "atualizar_produto", somente_autenticado(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/produtos/<int:produto_id>", "deletar_produto", somente_autenticado(controller.deletar), methods=["DELETE"]
    )
    return bp
