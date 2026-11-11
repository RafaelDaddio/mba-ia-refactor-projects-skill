"""Model de categorias: entidade, serialização e consultas."""
from sqlalchemy import func, select

from database import commit, db
from utils.helpers import utc_now

DEFAULT_COLOR = '#000000'


class Category(db.Model):
    __tablename__ = 'categories'

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

    # --- consultas -------------------------------------------------------------

    @classmethod
    def find_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_page(cls, limit=None, offset=0):
        stmt = select(cls).order_by(cls.id)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.scalar(select(func.count(cls.id)))

    # --- escrita -----------------------------------------------------------------

    def save(self):
        db.session.add(self)
        commit()

    def delete(self):
        # tasks da categoria ficam sem categoria (category_id = NULL), como antes
        db.session.delete(self)
        commit()
