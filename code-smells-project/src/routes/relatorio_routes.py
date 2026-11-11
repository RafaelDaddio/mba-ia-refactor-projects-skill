from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("relatorios", __name__)
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", controller.vendas, methods=["GET"])
    return bp
