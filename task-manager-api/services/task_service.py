"""Regras de tasks: CRUD, referências e estatísticas."""
import logging

from models.task import DONE_STATUS, STATUSES
from services.category_service import CATEGORY_NOT_FOUND
from services.user_service import USER_NOT_FOUND
from utils.errors import AppError, persistence_failure
from utils.helpers import calculate_percentage, utc_now

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'


class TaskService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def list_tasks(self, limit=None, offset=0):
        return self.tasks.list_with_relations(limit, offset)

    def get_task(self, task_id):
        task = self.tasks.find_by_id(task_id)
        if task is None:
            raise AppError(TASK_NOT_FOUND, status=404)
        return task

    def search(self, **filters):
        return self.tasks.search(**filters)

    def create_task(self, fields):
        self._check_references(fields)
        task = self.tasks()
        self._apply(task, fields)
        with persistence_failure('Erro ao criar task'):
            task.save()
        logger.info('Task criada: %s', task.id)
        return task

    def update_task(self, task_id, fields):
        task = self.get_task(task_id)
        self._check_references(fields)
        self._apply(task, fields)
        task.updated_at = utc_now()
        with persistence_failure('Erro ao atualizar'):
            task.save()
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        with persistence_failure('Erro ao deletar'):
            task.delete()
        logger.info('Task deletada: %s', task_id)

    def stats(self):
        total = self.tasks.count_all()
        by_status = self.tasks.count_by_status()
        return {
            'total': total,
            **{status: by_status.get(status, 0) for status in STATUSES},
            'overdue': self.tasks.count_overdue(utc_now()),
            'completion_rate': calculate_percentage(by_status.get(DONE_STATUS, 0), total),
        }

    def _check_references(self, fields):
        """Usuário e categoria informados precisam existir (inclusive o id 0)."""
        user_id = fields.get('user_id')
        if user_id is not None and self.users.find_by_id(user_id) is None:
            raise AppError(USER_NOT_FOUND, status=404)
        category_id = fields.get('category_id')
        if category_id is not None and self.categories.find_by_id(category_id) is None:
            raise AppError(CATEGORY_NOT_FOUND, status=404)

    @staticmethod
    def _apply(task, fields):
        for name, value in fields.items():
            if name == 'tags':
                task.set_tags(value)
            else:
                setattr(task, name, value)
