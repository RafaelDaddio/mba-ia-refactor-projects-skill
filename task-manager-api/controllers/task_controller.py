"""Fluxo HTTP de /tasks: leitura e validação da entrada, chamada ao service e resposta."""
from datetime import datetime

from flask import jsonify, request

from models.category import Category
from models.task import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    STATUSES,
    Task,
)
from models.user import User
from services.category_service import CATEGORY_NOT_FOUND
from services.task_service import TaskService
from services.user_service import USER_NOT_FOUND
from utils.errors import AppError
from utils.helpers import utc_now
from utils.validators import is_integer, optional_text, pagination, query_int, require_object

DATE_FORMAT = '%Y-%m-%d'


def _service():
    return TaskService(tasks=Task, users=User, categories=Category)


def _with_overdue(task, now=None):
    return {**task.to_dict(), 'overdue': task.is_overdue(now)}


# --- endpoints -------------------------------------------------------------------

def list_tasks():
    limit, offset = pagination(request.args)
    now = utc_now()
    result = []
    for task in _service().list_tasks(limit, offset):
        item = _with_overdue(task, now)
        item['user_name'] = task.user.name if task.user else None
        item['category_name'] = task.category.name if task.category else None
        result.append(item)
    return jsonify(result), 200


def get_task(task_id):
    return jsonify(_with_overdue(_service().get_task(task_id))), 200


def create_task():
    fields = _new_task_fields(require_object(request.get_json()))
    task = _service().create_task(fields)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    service = _service()
    service.get_task(task_id)  # 404 antes de validar o corpo, como antes
    fields = _task_changes(require_object(request.get_json()))
    task = service.update_task(task_id, fields)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    _service().delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    args = request.args
    priority = query_int(args, 'priority')
    user_id = query_int(args, 'user_id')
    limit, offset = pagination(args)
    tasks = _service().search(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=priority,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(_service().stats()), 200


# --- validação da entrada --------------------------------------------------------

def _new_task_fields(data):
    title = data.get('title')
    if not title:
        raise AppError('Título é obrigatório')
    fields = {
        'title': _title(title),
        'description': optional_text(data.get('description', ''), 'Descrição inválida'),
        'status': _status(data.get('status', DEFAULT_STATUS)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _reference(data.get('user_id'), USER_NOT_FOUND),
        'category_id': _reference(data.get('category_id'), CATEGORY_NOT_FOUND),
        'due_date': _due_date(data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD'),
    }
    tags = data.get('tags')
    if tags:
        fields['tags'] = _tags(tags)
    return fields


def _task_changes(data):
    parsers = {
        'title': _title,
        'description': lambda value: optional_text(value, 'Descrição inválida'),
        'status': _status,
        'priority': _priority,
        'user_id': lambda value: _reference(value, USER_NOT_FOUND),
        'category_id': lambda value: _reference(value, CATEGORY_NOT_FOUND),
        'due_date': lambda value: _due_date(value, 'Formato de data inválido'),
        'tags': _tags,
    }
    return {field: parse(data[field]) for field, parse in parsers.items() if field in data}


def _title(value):
    if not isinstance(value, str):
        raise AppError('Título inválido')
    if len(value) < MIN_TITLE_LENGTH:
        raise AppError('Título muito curto')
    if len(value) > MAX_TITLE_LENGTH:
        raise AppError('Título muito longo')
    return value


def _status(value):
    if value not in STATUSES:
        raise AppError('Status inválido')
    return value


def _priority(value):
    if not is_integer(value):
        raise AppError('Prioridade inválida')
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise AppError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return value


def _reference(value, not_found_message):
    """Id de usuário/categoria: None remove a referência; o que não for id válido não existe (404)."""
    if value is None:
        return None
    if is_integer(value):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    raise AppError(not_found_message, status=404)


def _due_date(value, message):
    if not value:
        return None
    if not isinstance(value, str):
        raise AppError(message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise AppError(message) from None


def _tags(value):
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise AppError('Tags inválidas')
        return value
    return optional_text(value, 'Tags inválidas')
