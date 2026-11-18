from datetime import datetime

from flask import jsonify, request

from utils.errors import AppError
from utils.validators import is_int, json_body, optional_id, optional_str, pagination, query_int

DUE_DATE_FORMAT = '%Y-%m-%d'


def _task_detail(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def _task_listing(task):
    data = _task_detail(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def _parse_due_date(value, message):
    if not value:
        return None
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise AppError(message, status=400) from None


def _parse_tags(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ','.join(value)
    raise AppError('Tags inválidas', status=400)


def _parse_task_fields(data, creating):
    """Confere presença e tipos; só os campos enviados entram no resultado."""
    fields = {}

    if creating or 'title' in data:
        title = data.get('title')
        if creating and not title:
            raise AppError('Título é obrigatório', status=400)
        if not isinstance(title, str):
            raise AppError('Título inválido', status=400)
        fields['title'] = title

    if 'description' in data:
        fields['description'] = optional_str(data['description'], 'Descrição inválida')

    if 'status' in data:
        if not isinstance(data['status'], str):
            raise AppError('Status inválido', status=400)
        fields['status'] = data['status']

    if 'priority' in data:
        if not is_int(data['priority']):
            raise AppError('Prioridade inválida', status=400)
        fields['priority'] = data['priority']

    if 'user_id' in data:
        fields['user_id'] = optional_id(data['user_id'], 'Usuário inválido')

    if 'category_id' in data:
        fields['category_id'] = optional_id(data['category_id'], 'Categoria inválida')

    if 'due_date' in data:
        message = 'Formato de data inválido. Use YYYY-MM-DD' if creating else 'Formato de data inválido'
        fields['due_date'] = _parse_due_date(data['due_date'], message)

    if 'tags' in data:
        tags = _parse_tags(data['tags'])
        fields['tags'] = (tags or None) if creating else tags

    return fields


class TaskController:
    def __init__(self, task_service):
        self.tasks = task_service

    def list_tasks(self):
        limit, offset = pagination(request.args)
        return jsonify([_task_listing(task) for task in self.tasks.list_tasks(limit, offset)]), 200

    def get_task(self, task_id):
        return jsonify(_task_detail(self.tasks.get(task_id))), 200

    def create_task(self):
        data = json_body(request)
        task = self.tasks.create(_parse_task_fields(data, creating=True))
        return jsonify(task.to_dict()), 201

    def update_task(self, task_id):
        task = self.tasks.get(task_id)
        data = json_body(request)
        task = self.tasks.update(task, _parse_task_fields(data, creating=False))
        return jsonify(task.to_dict()), 200

    def delete_task(self, task_id):
        self.tasks.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search_tasks(self):
        limit, offset = pagination(request.args)
        tasks = self.tasks.search(
            term=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=query_int(request.args, 'priority'),
            user_id=query_int(request.args, 'user_id'),
            limit=limit,
            offset=offset,
        )
        return jsonify([task.to_dict() for task in tasks]), 200

    def task_stats(self):
        return jsonify(self.tasks.stats()), 200
