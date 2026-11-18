from sqlalchemy import func, select

from database import db
from models.task import Task
from utils.time import utc_now


class Category(db.Model):
    __tablename__ = 'categories'

    DEFAULT_COLOR = '#000000'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }


class CategoryRepository:
    """Acesso a dados de categorias."""

    def __init__(self, session):
        self.session = session

    def get(self, category_id):
        return self.session.get(Category, category_id)

    def count_all(self):
        return self.session.execute(select(func.count(Category.id))).scalar_one()

    def list_with_task_count(self, limit, offset):
        """Pares (categoria, quantidade de tasks) numa única consulta."""
        query = (
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
            .limit(limit)
            .offset(offset)
        )
        return self.session.execute(query).all()

    def save(self, category):
        self.session.add(category)
        self.session.commit()
        return category

    def delete(self, category):
        self.session.delete(category)
        self.session.commit()
