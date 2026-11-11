"""Model de tasks: entidade, serialização e consultas."""
from sqlalchemy import case, func, select
from sqlalchemy.orm import selectinload

from database import commit, db
from utils.helpers import format_date, utc_now

STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
DEFAULT_STATUS = 'pending'
DONE_STATUS = 'done'
CLOSED_STATUSES = ('done', 'cancelled')  # tasks nesses status nunca ficam atrasadas
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
TAG_SEPARATOR = ','


def _paginate(stmt, limit, offset):
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset:
        stmt = stmt.offset(offset)
    return stmt


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
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
            'due_date': format_date(self.due_date),
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }

    def set_tags(self, tags):
        """Lista de tags vira texto separado por vírgula; texto ou None são gravados como vieram."""
        self.tags = TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        now = now or utc_now()
        return self.due_date < now and self.status not in CLOSED_STATUSES

    @classmethod
    def overdue_clause(cls, now):
        """Mesma regra de `is_overdue`, em SQL."""
        return db.and_(
            cls.due_date.is_not(None),
            cls.due_date < now,
            db.or_(cls.status.is_(None), cls.status.not_in(CLOSED_STATUSES)),
        )

    # --- consultas -------------------------------------------------------------

    @classmethod
    def find_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls, limit=None, offset=0):
        stmt = (
            select(cls)
            .options(selectinload(cls.user), selectinload(cls.category))
            .order_by(cls.id)
        )
        return db.session.execute(_paginate(stmt, limit, offset)).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None, limit=None, offset=0):
        stmt = select(cls)
        if text:
            pattern = f'%{text}%'
            stmt = stmt.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        stmt = _paginate(stmt.order_by(cls.id), limit, offset)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def find_by_user(cls, user_id, limit=None, offset=0):
        stmt = select(cls).where(cls.user_id == user_id).order_by(cls.id)
        return db.session.execute(_paginate(stmt, limit, offset)).scalars().all()

    @classmethod
    def find_overdue(cls, now):
        stmt = select(cls).where(cls.overdue_clause(now)).order_by(cls.id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(select(func.count(cls.id)))

    @classmethod
    def count_overdue(cls, now):
        return db.session.scalar(select(func.count(cls.id)).where(cls.overdue_clause(now)))

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(select(cls.status, func.count(cls.id)).group_by(cls.status))
        return dict(rows.all())

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(select(cls.priority, func.count(cls.id)).group_by(cls.priority))
        return dict(rows.all())

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(select(cls.category_id, func.count(cls.id)).group_by(cls.category_id))
        return dict(rows.all())

    @classmethod
    def count_by_user(cls):
        """{user_id: (total de tasks, tasks concluídas)} numa única consulta."""
        done = func.sum(case((cls.status == DONE_STATUS, 1), else_=0))
        rows = db.session.execute(select(cls.user_id, func.count(cls.id), done).group_by(cls.user_id))
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def count_recent_activity(cls, since):
        """(tasks criadas desde `since`, tasks concluídas e atualizadas desde `since`)."""
        created = func.sum(case((cls.created_at >= since, 1), else_=0))
        completed = func.sum(case((db.and_(cls.status == DONE_STATUS, cls.updated_at >= since), 1), else_=0))
        row = db.session.execute(select(created, completed)).one()
        return row[0] or 0, row[1] or 0

    # --- escrita -----------------------------------------------------------------

    def save(self):
        db.session.add(self)
        commit()

    def delete(self):
        db.session.delete(self)
        commit()
