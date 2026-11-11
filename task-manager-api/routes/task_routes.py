from flask import Blueprint

from controllers import task_controller

bp = Blueprint('tasks', __name__)

bp.add_url_rule('/tasks', view_func=task_controller.list_tasks, methods=['GET'])
bp.add_url_rule('/tasks', view_func=task_controller.create_task, methods=['POST'])
bp.add_url_rule('/tasks/search', view_func=task_controller.search_tasks, methods=['GET'])
bp.add_url_rule('/tasks/stats', view_func=task_controller.task_stats, methods=['GET'])
bp.add_url_rule('/tasks/<int:task_id>', view_func=task_controller.get_task, methods=['GET'])
bp.add_url_rule('/tasks/<int:task_id>', view_func=task_controller.update_task, methods=['PUT'])
bp.add_url_rule('/tasks/<int:task_id>', view_func=task_controller.delete_task, methods=['DELETE'])
