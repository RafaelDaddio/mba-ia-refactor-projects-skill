"""Fluxo HTTP de /users e /login."""
from flask import jsonify, request

from middlewares.auth import is_admin_request
from models.task import Task
from models.user import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, ROLES, User
from services.user_service import UserService
from utils.errors import AppError
from utils.helpers import utc_now
from utils.validators import is_valid_email, pagination, require_object

# campos de task devolvidos em /users/<id>/tasks
USER_TASK_FIELDS = ('id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date')


def _service():
    return UserService(users=User, tasks=Task)


# --- endpoints -------------------------------------------------------------------

def list_users():
    limit, offset = pagination(request.args)
    users = _service().list_users(limit, offset)
    return jsonify([{**user.to_dict(), 'task_count': task_count} for user, task_count in users]), 200


def get_user(user_id):
    service = _service()
    data = service.get_user(user_id).to_dict()
    data['tasks'] = [task.to_dict() for task in service.list_user_tasks(user_id)]
    return jsonify(data), 200


def create_user():
    data = require_object(request.get_json())
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise AppError('Nome é obrigatório')
    if not email:
        raise AppError('Email é obrigatório')
    if not password:
        raise AppError('Senha é obrigatória')
    if not isinstance(name, str):
        raise AppError('Nome inválido')
    if not is_valid_email(email):
        raise AppError('Email inválido')
    if not isinstance(password, str):
        raise AppError('Senha inválida')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    if role not in ROLES:
        raise AppError('Role inválido')

    user = _service().create_user(name, email, password, role, actor_is_admin=is_admin_request())
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    service = _service()
    service.get_user(user_id)  # 404 antes de validar o corpo, como antes
    fields = _user_changes(require_object(request.get_json()))
    user = service.update_user(user_id, fields, actor_is_admin=is_admin_request())
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    _service().delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    limit, offset = pagination(request.args)
    now = utc_now()
    result = []
    for task in _service().list_user_tasks(user_id, limit, offset):
        full = task.to_dict()
        item = {field: full[field] for field in USER_TASK_FIELDS}
        item['overdue'] = task.is_overdue(now)
        result.append(item)
    return jsonify(result), 200


def login():
    data = require_object(request.get_json())
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise AppError('Email e senha são obrigatórios')

    user, token = _service().login(email, password)
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200


# --- validação da entrada --------------------------------------------------------

def _user_changes(data):
    fields = {}
    if 'name' in data:
        if not data['name']:
            raise AppError('Nome é obrigatório')
        if not isinstance(data['name'], str):
            raise AppError('Nome inválido')
        fields['name'] = data['name']
    if 'email' in data:
        if not is_valid_email(data['email']):
            raise AppError('Email inválido')
        fields['email'] = data['email']
    if 'password' in data:
        if not isinstance(data['password'], str):
            raise AppError('Senha inválida')
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise AppError('Senha muito curta')
        fields['password'] = data['password']
    if 'role' in data:
        if data['role'] not in ROLES:
            raise AppError('Role inválido')
        fields['role'] = data['role']
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise AppError('Active inválido')
        fields['active'] = data['active']
    return fields
