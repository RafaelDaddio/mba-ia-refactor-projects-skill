from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from database import db
from utils.time import utc_now


class Task(db.Model):
    __tablename__ = 'tasks'

    VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
    CLOSED_STATUSES = ('done', 'cancelled')
    DONE_STATUS = 'done'
    DEFAULT_STATUS = 'pending'
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5
    DEFAULT_PRIORITY = 3
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 200

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    @classmethod
    def validate_status(cls, new_status):
        return new_status in cls.VALID_STATUSES

    @classmethod
    def validate_priority(cls, priority):
        return cls.MIN_PRIORITY <= priority <= cls.MAX_PRIORITY

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        if self.status in self.CLOSED_STATUSES:
            return False
        return self.due_date < (now or utc_now())


class TaskRepository:
    """Acesso a dados de tasks."""

    def __init__(self, session):
        self.session = session

    def get(self, task_id):
        return self.session.get(Task, task_id)

    def list_with_relations(self, limit, offset):
        """Tasks com usuário e categoria já carregados (sem uma consulta por linha)."""
        query = (
            select(Task)
            .options(selectinload(Task.user), selectinload(Task.category))
            .order_by(Task.id)
            .limit(limit)
            .offset(offset)
        )
        return self.session.execute(query).scalars().all()

    def search(self, term, status, priority, user_id, limit, offset):
        query = select(Task)
        if term:
            pattern = f'%{term}%'
            query = query.where(or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        query = query.order_by(Task.id).limit(limit).offset(offset)
        return self.session.execute(query).scalars().all()

    def list_by_user(self, user_id, limit=None, offset=0):
        query = select(Task).where(Task.user_id == user_id).order_by(Task.id)
        if limit is not None:
            query = query.limit(limit).offset(offset)
        return self.session.execute(query).scalars().all()

    def count_all(self):
        return self.session.execute(select(func.count(Task.id))).scalar_one()

    def count_by_status(self):
        rows = self.session.execute(select(Task.status, func.count(Task.id)).group_by(Task.status))
        return {status: count for status, count in rows}

    def count_by_priority(self):
        rows = self.session.execute(select(Task.priority, func.count(Task.id)).group_by(Task.priority))
        return {priority: count for priority, count in rows}

    @staticmethod
    def _overdue_filter(now):
        # mesma regra de Task.is_overdue, aplicada no banco
        return (Task.due_date < now, Task.status.notin_(Task.CLOSED_STATUSES))

    def count_overdue(self, now):
        query = select(func.count(Task.id)).where(*self._overdue_filter(now))
        return self.session.execute(query).scalar_one()

    def list_overdue(self, now):
        query = select(Task).where(*self._overdue_filter(now)).order_by(Task.id)
        return self.session.execute(query).scalars().all()

    def count_created_since(self, since):
        query = select(func.count(Task.id)).where(Task.created_at >= since)
        return self.session.execute(query).scalar_one()

    def count_done_updated_since(self, since):
        query = select(func.count(Task.id)).where(
            Task.status == Task.DONE_STATUS, Task.updated_at >= since
        )
        return self.session.execute(query).scalar_one()

    def save(self, task):
        self.session.add(task)
        self.session.commit()
        return task

    def delete(self, task):
        self.session.delete(task)
        self.session.commit()
