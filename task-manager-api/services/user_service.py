import logging

from models.user import User
from utils.errors import AppError

logger = logging.getLogger(__name__)


class UserService:
    """Regras de negócio de usuários."""

    def __init__(self, users, tasks):
        self.users = users
        self.tasks = tasks

    def list_users(self, limit, offset):
        return self.users.list_with_task_count(limit, offset)

    def get(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise AppError('Usuário não encontrado', status=404)
        return user

    def tasks_of(self, user, limit, offset):
        return self.tasks.list_by_user(user.id, limit, offset)

    @staticmethod
    def changes_role(requested_role, current_role=User.DEFAULT_ROLE):
        """Diz se o papel pedido difere do atual (ou do padrão, no cadastro)."""
        return requested_role != current_role

    def create(self, fields):
        self._check_password(
            fields['password'], f'Senha deve ter no mínimo {User.MIN_PASSWORD_LENGTH} caracteres'
        )
        self._check_email_available(fields['email'])
        role = fields.get('role', User.DEFAULT_ROLE)
        self._check_role(role)

        user = User(name=fields['name'], email=fields['email'], role=role)
        user.set_password(fields['password'])
        self.users.save(user)
        logger.info('Usuário criado: %s', user.id)
        return user

    def update(self, user, fields):
        if 'email' in fields:
            self._check_email_available(fields['email'], ignore_id=user.id)
        if 'password' in fields:
            self._check_password(fields['password'], 'Senha muito curta')
        if 'role' in fields:
            self._check_role(fields['role'])

        for name in ('name', 'email', 'role', 'active'):
            if name in fields:
                setattr(user, name, fields[name])
        if 'password' in fields:
            user.set_password(fields['password'])
        self.users.save(user)
        logger.info('Usuário atualizado: %s', user.id)
        return user

    def delete(self, user_id):
        user = self.get(user_id)
        self.users.delete_with_tasks(user)
        logger.info('Usuário deletado: %s', user_id)

    @staticmethod
    def _check_password(password, message):
        if len(password) < User.MIN_PASSWORD_LENGTH:
            raise AppError(message, status=400)

    @staticmethod
    def _check_role(role):
        if role not in User.VALID_ROLES:
            raise AppError('Role inválido', status=400)

    def _check_email_available(self, email, ignore_id=None):
        existing = self.users.find_by_email(email)
        if existing is not None and existing.id != ignore_id:
            raise AppError('Email já cadastrado', status=409)
