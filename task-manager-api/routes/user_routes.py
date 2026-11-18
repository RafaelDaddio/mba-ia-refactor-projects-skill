from flask import Blueprint

from middlewares.auth import admin_only, owner_only


def create_blueprint(controller):
    bp = Blueprint('users', __name__)
    # administrador: reúne dados de todas as contas
    bp.add_url_rule('/users', view_func=admin_only(controller.list_users), methods=['GET'])
    # pública: cadastro (definir `role` exige administrador, conferido no controller)
    bp.add_url_rule('/users', view_func=controller.create_user, methods=['POST'])
    # dono da conta ou administrador
    bp.add_url_rule('/users/<int:user_id>', view_func=owner_only(controller.get_user), methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', view_func=owner_only(controller.update_user), methods=['PUT'])
    bp.add_url_rule('/users/<int:user_id>', view_func=owner_only(controller.delete_user), methods=['DELETE'])
    # pública: tasks atribuídas não pertencem à conta e saem sem dados pessoais
    bp.add_url_rule('/users/<int:user_id>/tasks', view_func=controller.get_user_tasks, methods=['GET'])
    return bp
