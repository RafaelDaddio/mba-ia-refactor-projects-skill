"""Rotas de pedidos."""
from flask import Blueprint

from src.middlewares.auth import somente_admin, somente_dono


def criar_blueprint(controller):
    bp = Blueprint("pedidos", __name__)
    # dono ou administrador: a conta vem do corpo (`usuario_id`), conferida no controller
    bp.add_url_rule("/pedidos", "criar_pedido", controller.criar, methods=["POST"])
    # pedidos de todas as contas: administrador
    bp.add_url_rule("/pedidos", "listar_todos_pedidos", somente_admin(controller.listar_todos), methods=["GET"])
    bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_pedidos_usuario",
        somente_dono("usuario_id")(controller.listar_do_usuario),
        methods=["GET"],
    )
    # dono do pedido ou administrador: o dono vem do pedido, conferido no controller
    bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controller.atualizar_status, methods=["PUT"]
    )
    return bp
