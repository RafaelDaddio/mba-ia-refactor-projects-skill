"""Model de usuários: entidade, senha, serialização e consultas."""
import hashlib
import hmac
import string

from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from database import commit, db
from models.task import Task
from utils.helpers import utc_now

ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
MIN_PASSWORD_LENGTH = 4
_LEGACY_MD5_LENGTH = 32


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # o hash da senha nunca sai nas respostas
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self.has_legacy_password_hash():
            legacy = hashlib.md5(pwd.encode()).hexdigest()  # só para validar hashes antigos
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)

    def has_legacy_password_hash(self):
        """Hash MD5 sem salt gravado pela versão anterior (32 caracteres hexadecimais)."""
        stored = self.password or ''
        return len(stored) == _LEGACY_MD5_LENGTH and all(c in string.hexdigits for c in stored)

    # --- consultas -------------------------------------------------------------

    @classmethod
    def find_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(select(cls).where(cls.email == email)).scalars().first()

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
        return db.session.scalar(select(db.func.count(cls.id)))

    # --- escrita -----------------------------------------------------------------

    def save(self):
        db.session.add(self)
        commit()

    def delete_with_tasks(self):
        """Exclui o usuário e as tasks dele na mesma transação."""
        for task in db.session.execute(select(Task).where(Task.user_id == self.id)).scalars():
            db.session.delete(task)
        db.session.delete(self)
        commit()
