from flask import Blueprint

from controllers import health_controller

bp = Blueprint('health', __name__)

bp.add_url_rule('/health', view_func=health_controller.health, methods=['GET'])
bp.add_url_rule('/', view_func=health_controller.index, methods=['GET'])
