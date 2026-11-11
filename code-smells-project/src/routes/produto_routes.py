from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__)
    bp.add_url_rule("/produtos", "listar_produtos", controller.listar, methods=["GET"])
    bp.add_url_rule("/produtos/busca", "buscar_produtos", controller.buscar, methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", controller.obter, methods=["GET"])
    bp.add_url_rule("/produtos", "criar_produto", controller.criar, methods=["POST"])
    bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", controller.atualizar, methods=["PUT"])
    bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", controller.excluir, methods=["DELETE"])
    return bp
