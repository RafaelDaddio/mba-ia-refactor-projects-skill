from flask import Blueprint

from middlewares.auth import user_only


def create_blueprint(controller):
    bp = Blueprint('categories', __name__)
    # pública
    bp.add_url_rule('/categories', view_func=controller.list_categories, methods=['GET'])
    # conta autenticada: escritas
    bp.add_url_rule('/categories', view_func=user_only(controller.create_category), methods=['POST'])
    bp.add_url_rule(
        '/categories/<int:cat_id>', view_func=user_only(controller.update_category), methods=['PUT']
    )
    bp.add_url_rule(
        '/categories/<int:cat_id>', view_func=user_only(controller.delete_category), methods=['DELETE']
    )
    return bp
