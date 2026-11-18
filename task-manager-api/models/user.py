from sqlalchemy import case, func, select
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.task import Task
from utils.time import utc_now


class User(db.Model):
    __tablename__ = 'users'

    VALID_ROLES = ('user', 'admin', 'manager')
    DEFAULT_ROLE = 'user'
    ADMIN_ROLE = 'admin'
    MIN_PASSWORD_LENGTH = 4

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # o hash da senha nunca sai do model
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == self.ADMIN_ROLE


class UserRepository:
    """Acesso a dados de usuários."""

    def __init__(self, session):
        self.session = session

    def get(self, user_id):
        return self.session.get(User, user_id)

    def find_by_email(self, email):
        return self.session.execute(select(User).where(User.email == email)).scalars().first()

    def count_all(self):
        return self.session.execute(select(func.count(User.id))).scalar_one()

    def list_with_task_count(self, limit, offset):
        """Pares (usuário, quantidade de tasks) numa única consulta."""
        query = (
            select(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
        return self.session.execute(query).all()

    def task_totals(self):
        """Linhas (id, nome, total de tasks, tasks concluídas) por usuário numa única consulta."""
        completed = func.coalesce(func.sum(case((Task.status == Task.DONE_STATUS, 1), else_=0)), 0)
        query = (
            select(User.id, User.name, func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        return self.session.execute(query).all()

    def save(self, user):
        self.session.add(user)
        self.session.commit()
        return user

    def delete_with_tasks(self, user):
        """Exclui o usuário e as tasks atribuídas a ele na mesma transação."""
        for task in self.session.execute(select(Task).where(Task.user_id == user.id)).scalars():
            self.session.delete(task)
        self.session.delete(user)
        self.session.commit()
