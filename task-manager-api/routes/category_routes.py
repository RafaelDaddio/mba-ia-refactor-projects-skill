from flask import Blueprint

from controllers import category_controller

bp = Blueprint('categories', __name__)

bp.add_url_rule('/categories', view_func=category_controller.list_categories, methods=['GET'])
bp.add_url_rule('/categories', view_func=category_controller.create_category, methods=['POST'])
bp.add_url_rule('/categories/<int:cat_id>', view_func=category_controller.update_category, methods=['PUT'])
bp.add_url_rule('/categories/<int:cat_id>', view_func=category_controller.delete_category, methods=['DELETE'])
