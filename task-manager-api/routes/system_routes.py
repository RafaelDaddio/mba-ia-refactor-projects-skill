from flask import Blueprint

from controllers import system_controller


def create_blueprint():
    bp = Blueprint('system', __name__)
    bp.add_url_rule('/health', view_func=system_controller.health, methods=['GET'])
    bp.add_url_rule('/', view_func=system_controller.index, methods=['GET'])
    return bp
