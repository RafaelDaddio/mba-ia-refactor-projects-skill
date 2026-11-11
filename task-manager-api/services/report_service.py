"""Relatórios de tasks e produtividade."""
from collections import Counter
from datetime import timedelta

from models.task import DONE_STATUS, STATUSES
from services.user_service import USER_NOT_FOUND
from utils.errors import AppError
from utils.helpers import calculate_percentage, utc_now

RECENT_ACTIVITY_DAYS = 7
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como alta
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


class ReportService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        now = utc_now()
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()
        overdue = self.tasks.find_overdue(now)
        created_recently, completed_recently = self.tasks.count_recent_activity(
            now - timedelta(days=RECENT_ACTIVITY_DAYS)
        )
        per_user = self.tasks.count_by_user()

        productivity = []
        for user in self.users.list_page():
            total, completed = per_user.get(user.id, (0, 0))
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })

        return {
            'generated_at': str(utc_now()),
            'overview': {
                'total_tasks': self.tasks.count_all(),
                'total_users': self.users.count_all(),
                'total_categories': self.categories.count_all(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in STATUSES},
            'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': created_recently,
                'tasks_completed_last_7_days': completed_recently,
            },
            'user_productivity': productivity,
        }

    def user_report(self, user_id):
        user = self.users.find_by_id(user_id)
        if user is None:
            raise AppError(USER_NOT_FOUND, status=404)

        tasks = self.tasks.find_by_user(user_id)
        now = utc_now()
        by_status = Counter(task.status for task in tasks)
        total = len(tasks)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                **{status: by_status[status] for status in STATUSES},
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': calculate_percentage(by_status[DONE_STATUS], total),
            },
        }
