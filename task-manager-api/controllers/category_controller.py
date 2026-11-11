"""Fluxo HTTP de /categories."""
from flask import jsonify, request

from models.category import DEFAULT_COLOR, Category
from models.task import Task
from services.category_service import CategoryService
from utils.errors import AppError
from utils.validators import optional_text, pagination, require_object


def _service():
    return CategoryService(categories=Category, tasks=Task)


def list_categories():
    limit, offset = pagination(request.args)
    categories = _service().list_categories(limit, offset)
    return jsonify([{**category.to_dict(), 'task_count': task_count} for category, task_count in categories]), 200


def create_category():
    data = require_object(request.get_json())
    name = _name(data.get('name'))
    description = optional_text(data.get('description', ''), 'Descrição inválida')
    color = optional_text(data.get('color', DEFAULT_COLOR), 'Cor inválida')
    category = _service().create_category(name, description, color)
    return jsonify(category.to_dict()), 201


def update_category(cat_id):
    service = _service()
    service.get_category(cat_id)  # 404 antes de validar o corpo, como antes
    data = require_object(request.get_json())
    fields = {}
    if 'name' in data:
        fields['name'] = _name(data['name'])
    if 'description' in data:
        fields['description'] = optional_text(data['description'], 'Descrição inválida')
    if 'color' in data:
        fields['color'] = optional_text(data['color'], 'Cor inválida')
    category = service.update_category(cat_id, fields)
    return jsonify(category.to_dict()), 200


def delete_category(cat_id):
    _service().delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200


def _name(value):
    if not value:
        raise AppError('Nome é obrigatório')
    if not isinstance(value, str):
        raise AppError('Nome inválido')
    return value
