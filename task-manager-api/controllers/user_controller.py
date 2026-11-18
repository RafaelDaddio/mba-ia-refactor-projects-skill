from flask import jsonify, request

from middlewares.auth import require_admin
from utils.errors import AppError
from utils.helpers import validate_email
from utils.validators import json_body, pagination


def _user_listing(user, task_count):
    data = user.to_dict()
    data['task_count'] = task_count
    return data


def _task_summary(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'overdue': task.is_overdue(),
    }


def _parse_name(value):
    if not value:
        raise AppError('Nome é obrigatório', status=400)
    if not isinstance(value, str):
        raise AppError('Nome inválido', status=400)
    return value


def _parse_email(value):
    if not isinstance(value, str) or not validate_email(value):
        raise AppError('Email inválido', status=400)
    return value


def _parse_password(value):
    if not isinstance(value, str):
        raise AppError('Senha inválida', status=400)
    return value


def _parse_role(value):
    if not isinstance(value, str):
        raise AppError('Role inválido', status=400)
    return value


def _parse_new_user(data):
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name:
        raise AppError('Nome é obrigatório', status=400)
    if not email:
        raise AppError('Email é obrigatório', status=400)
    if not password:
        raise AppError('Senha é obrigatória', status=400)
    fields = {
        'name': _parse_name(name),
        'email': _parse_email(email),
        'password': _parse_password(password),
    }
    if 'role' in data:
        fields['role'] = _parse_role(data['role'])
    return fields


def _parse_user_changes(data):
    """Mesmas regras do cadastro, só para os campos enviados."""
    fields = {}
    if 'name' in data:
        fields['name'] = _parse_name(data['name'])
    if 'email' in data:
        fields['email'] = _parse_email(data['email'])
    if 'password' in data:
        fields['password'] = _parse_password(data['password'])
    if 'role' in data:
        fields['role'] = _parse_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise AppError('Campo active deve ser booleano', status=400)
        fields['active'] = data['active']
    return fields


class UserController:
    def __init__(self, user_service):
        self.users = user_service

    def list_users(self):
        limit, offset = pagination(request.args)
        rows = self.users.list_users(limit, offset)
        return jsonify([_user_listing(user, task_count) for user, task_count in rows]), 200

    def get_user(self, user_id):
        user = self.users.get(user_id)
        limit, offset = pagination(request.args)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in self.users.tasks_of(user, limit, offset)]
        return jsonify(data), 200

    def create_user(self):
        data = json_body(request)
        # o cliente não define o próprio papel: só um administrador cadastra com papel diferente do padrão
        if 'role' in data and self.users.changes_role(data['role']):
            require_admin()
        user = self.users.create(_parse_new_user(data))
        return jsonify(user.to_dict()), 201

    def update_user(self, user_id):
        user = self.users.get(user_id)
        data = json_body(request)
        # mudar o papel exige administrador, inclusive para o dono da conta
        if 'role' in data and self.users.changes_role(data['role'], user.role):
            require_admin()
        user = self.users.update(user, _parse_user_changes(data))
        return jsonify(user.to_dict()), 200

    def delete_user(self, user_id):
        self.users.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def get_user_tasks(self, user_id):
        user = self.users.get(user_id)
        limit, offset = pagination(request.args)
        return jsonify([_task_summary(task) for task in self.users.tasks_of(user, limit, offset)]), 200
