from flask import jsonify, request

from utils.errors import AppError
from utils.validators import json_body, optional_str, pagination


def _category_listing(category, task_count):
    data = category.to_dict()
    data['task_count'] = task_count
    return data


def _parse_category_fields(data, creating):
    """Confere presença e tipos; só os campos enviados entram no resultado."""
    fields = {}
    if creating or 'name' in data:
        name = data.get('name')
        if not name:
            raise AppError('Nome é obrigatório', status=400)
        if not isinstance(name, str):
            raise AppError('Nome inválido', status=400)
        fields['name'] = name
    if 'description' in data:
        fields['description'] = optional_str(data['description'], 'Descrição inválida')
    if 'color' in data:
        fields['color'] = optional_str(data['color'], 'Cor inválida')
    return fields


class CategoryController:
    def __init__(self, category_service):
        self.categories = category_service

    def list_categories(self):
        limit, offset = pagination(request.args)
        rows = self.categories.list_categories(limit, offset)
        return jsonify([_category_listing(category, task_count) for category, task_count in rows]), 200

    def create_category(self):
        data = json_body(request)
        category = self.categories.create(_parse_category_fields(data, creating=True))
        return jsonify(category.to_dict()), 201

    def update_category(self, cat_id):
        category = self.categories.get(cat_id)
        data = json_body(request, allow_empty=True)  # corpo `{}` não altera nada, como antes
        category = self.categories.update(category, _parse_category_fields(data, creating=False))
        return jsonify(category.to_dict()), 200

    def delete_category(self, cat_id):
        self.categories.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
