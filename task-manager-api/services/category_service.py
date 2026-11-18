import logging

from models.category import Category
from utils.errors import AppError

logger = logging.getLogger(__name__)


class CategoryService:
    """Regras de negócio de categorias."""

    def __init__(self, categories):
        self.categories = categories

    def list_categories(self, limit, offset):
        return self.categories.list_with_task_count(limit, offset)

    def get(self, category_id):
        category = self.categories.get(category_id)
        if category is None:
            raise AppError('Categoria não encontrada', status=404)
        return category

    def create(self, fields):
        category = Category(
            name=fields['name'],
            description=fields.get('description', ''),
            color=fields.get('color', Category.DEFAULT_COLOR),
        )
        self.categories.save(category)
        logger.info('Categoria criada: %s', category.id)
        return category

    def update(self, category, fields):
        for name, value in fields.items():
            setattr(category, name, value)
        self.categories.save(category)
        logger.info('Categoria atualizada: %s', category.id)
        return category

    def delete(self, category_id):
        category = self.get(category_id)
        self.categories.delete(category)
        logger.info('Categoria deletada: %s', category_id)
