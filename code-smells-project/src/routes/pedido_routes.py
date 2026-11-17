"""Rotas de pedidos. A listagem geral é do administrador; as demais, do dono da conta ou administrador."""
from flask import Blueprint


def criar_blueprint(controller, auth):
    bp = Blueprint("pedidos", __name__)
    # dono da conta ou administrador: conferido no controller (conta do corpo, do caminho ou do pedido)
    bp.add_url_rule("/pedidos", view_func=controller.criar, methods=["POST"])
    bp.add_url_rule("/pedidos", view_func=auth.admin_only(controller.listar_todos), methods=["GET"])
    bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", view_func=controller.listar_do_usuario, methods=["GET"])
    bp.add_url_rule("/pedidos/<int:pedido_id>/status", view_func=controller.atualizar_status, methods=["PUT"])
    return bp
