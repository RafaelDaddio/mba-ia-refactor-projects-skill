from flask import Blueprint

from controllers import user_controller

bp = Blueprint('users', __name__)

bp.add_url_rule('/users', view_func=user_controller.list_users, methods=['GET'])
bp.add_url_rule('/users', view_func=user_controller.create_user, methods=['POST'])
bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.get_user, methods=['GET'])
bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.update_user, methods=['PUT'])
bp.add_url_rule('/users/<int:user_id>', view_func=user_controller.delete_user, methods=['DELETE'])
bp.add_url_rule('/users/<int:user_id>/tasks', view_func=user_controller.get_user_tasks, methods=['GET'])
bp.add_url_rule('/login', view_func=user_controller.login, methods=['POST'])
