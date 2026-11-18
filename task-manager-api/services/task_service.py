import logging

from models.task import Task
from utils.errors import AppError
from utils.helpers import calculate_percentage
from utils.time import utc_now

logger = logging.getLogger(__name__)


class TaskService:
    """Regras de negócio de tasks."""

    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def list_tasks(self, limit, offset):
        return self.tasks.list_with_relations(limit, offset)

    def get(self, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            raise AppError('Task não encontrada', status=404)
        return task

    def search(self, term, status, priority, user_id, limit, offset):
        return self.tasks.search(term, status, priority, user_id, limit, offset)

    def create(self, fields):
        self._check_fields(fields)
        task = Task(
            title=fields['title'],
            description=fields.get('description', ''),
            status=fields.get('status', Task.DEFAULT_STATUS),
            priority=fields.get('priority', Task.DEFAULT_PRIORITY),
            user_id=fields.get('user_id'),
            category_id=fields.get('category_id'),
            due_date=fields.get('due_date'),
            tags=fields.get('tags'),
        )
        self.tasks.save(task)
        logger.info('Task criada: %s', task.id)
        return task

    def update(self, task, fields):
        self._check_fields(fields)
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utc_now()
        self.tasks.save(task)
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete(self, task_id):
        task = self.get(task_id)
        self.tasks.delete(task)
        logger.info('Task deletada: %s', task_id)

    def stats(self):
        by_status = self.tasks.count_by_status()
        total = self.tasks.count_all()
        stats = {status: by_status.get(status, 0) for status in Task.VALID_STATUSES}
        stats['total'] = total
        stats['overdue'] = self.tasks.count_overdue(utc_now())
        stats['completion_rate'] = calculate_percentage(stats[Task.DONE_STATUS], total)
        return stats

    def _check_fields(self, fields):
        """Regras de domínio sobre os campos já tipados pelo controller (criação e atualização)."""
        if 'title' in fields:
            if len(fields['title']) < Task.MIN_TITLE_LENGTH:
                raise AppError('Título muito curto', status=400)
            if len(fields['title']) > Task.MAX_TITLE_LENGTH:
                raise AppError('Título muito longo', status=400)
        if 'status' in fields and not Task.validate_status(fields['status']):
            raise AppError('Status inválido', status=400)
        if 'priority' in fields and not Task.validate_priority(fields['priority']):
            raise AppError(
                f'Prioridade deve ser entre {Task.MIN_PRIORITY} e {Task.MAX_PRIORITY}', status=400
            )
        # None desfaz o vínculo; qualquer id informado precisa existir
        if fields.get('user_id') is not None and self.users.get(fields['user_id']) is None:
            raise AppError('Usuário não encontrado', status=404)
        if fields.get('category_id') is not None and self.categories.get(fields['category_id']) is None:
            raise AppError('Categoria não encontrada', status=404)
