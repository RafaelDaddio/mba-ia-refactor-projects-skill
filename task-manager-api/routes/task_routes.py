from flask import Blueprint

from middlewares.auth import user_only


def create_blueprint(controller):
    bp = Blueprint('tasks', __name__)
    # conta autenticada: a listagem traz o nome dos responsáveis
    bp.add_url_rule('/tasks', view_func=user_only(controller.list_tasks), methods=['GET'])
    # públicas: leituras sem dados pessoais
    bp.add_url_rule('/tasks/<int:task_id>', view_func=controller.get_task, methods=['GET'])
    bp.add_url_rule('/tasks/search', view_func=controller.search_tasks, methods=['GET'])
    bp.add_url_rule('/tasks/stats', view_func=controller.task_stats, methods=['GET'])
    # conta autenticada: escritas
    bp.add_url_rule('/tasks', view_func=user_only(controller.create_task), methods=['POST'])
    bp.add_url_rule('/tasks/<int:task_id>', view_func=user_only(controller.update_task), methods=['PUT'])
    bp.add_url_rule('/tasks/<int:task_id>', view_func=user_only(controller.delete_task), methods=['DELETE'])
    return bp
