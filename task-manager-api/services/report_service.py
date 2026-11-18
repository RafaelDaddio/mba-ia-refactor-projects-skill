from datetime import timedelta

from models.task import Task
from utils.errors import AppError
from utils.helpers import calculate_percentage
from utils.time import utc_now

PRIORITY_LABELS = ((1, 'critical'), (2, 'high'), (3, 'medium'), (4, 'low'), (5, 'minimal'))
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como alta prioridade
RECENT_ACTIVITY_DAYS = 7


class ReportService:
    """Relatórios de tasks e de produtividade."""

    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        now = utc_now()
        recent_since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()

        overdue_tasks = [
            {
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            }
            for task in self.tasks.list_overdue(now)
        ]

        user_productivity = [
            {
                'user_id': user_id,
                'user_name': user_name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            }
            for user_id, user_name, total, completed in self.users.task_totals()
        ]

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self.tasks.count_all(),
                'total_users': self.users.count_all(),
                'total_categories': self.categories.count_all(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in Task.VALID_STATUSES},
            'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': overdue_tasks,
            },
            'recent_activity': {
                'tasks_created_last_7_days': self.tasks.count_created_since(recent_since),
                'tasks_completed_last_7_days': self.tasks.count_done_updated_since(recent_since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise AppError('Usuário não encontrado', status=404)

        now = utc_now()
        tasks = self.tasks.list_by_user(user_id)
        statistics = {status: 0 for status in Task.VALID_STATUSES}
        overdue = 0
        high_priority = 0
        for task in tasks:
            if task.status in statistics:
                statistics[task.status] += 1
            if task.priority is not None and task.priority <= HIGH_PRIORITY_MAX:
                high_priority += 1
            if task.is_overdue(now):
                overdue += 1

        statistics['total_tasks'] = len(tasks)
        statistics['overdue'] = overdue
        statistics['high_priority'] = high_priority
        statistics['completion_rate'] = calculate_percentage(statistics[Task.DONE_STATUS], len(tasks))

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': statistics,
        }
