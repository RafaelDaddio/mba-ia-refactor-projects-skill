"""Regras de categorias."""
from utils.errors import AppError, persistence_failure

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryService:
    def __init__(self, categories, tasks):
        self.categories = categories
        self.tasks = tasks

    def list_categories(self, limit=None, offset=0):
        """[(categoria, total de tasks)] com as contagens numa única consulta."""
        counts = self.tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in self.categories.list_page(limit, offset)]

    def get_category(self, category_id):
        category = self.categories.find_by_id(category_id)
        if category is None:
            raise AppError(CATEGORY_NOT_FOUND, status=404)
        return category

    def create_category(self, name, description, color):
        category = self.categories(name=name, description=description, color=color)
        with persistence_failure('Erro ao criar categoria'):
            category.save()
        return category

    def update_category(self, category_id, fields):
        category = self.get_category(category_id)
        for name, value in fields.items():
            setattr(category, name, value)
        with persistence_failure('Erro ao atualizar'):
            category.save()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        with persistence_failure('Erro ao deletar'):
            category.delete()
