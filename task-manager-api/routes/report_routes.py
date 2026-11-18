from flask import Blueprint

from middlewares.auth import admin_only, owner_only


def create_blueprint(controller):
    bp = Blueprint('reports', __name__)
    # administrador: produtividade de todas as contas
    bp.add_url_rule('/reports/summary', view_func=admin_only(controller.summary_report), methods=['GET'])
    # dono da conta ou administrador
    bp.add_url_rule(
        '/reports/user/<int:user_id>', view_func=owner_only(controller.user_report), methods=['GET']
    )
    return bp
