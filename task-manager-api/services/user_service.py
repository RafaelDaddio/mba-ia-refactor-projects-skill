"""Regras de usuários: cadastro, atualização, exclusão e login."""
import logging

from models.user import DEFAULT_ROLE
from utils.errors import AppError, PersistenceError, persistence_failure

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
# Token de fachada mantido por contrato; autenticação real é pendência (F05).
TOKEN_PREFIX = 'fake-jwt-token-'


class UserService:
    def __init__(self, users, tasks):
        self.users = users
        self.tasks = tasks

    def list_users(self, limit=None, offset=0):
        """[(usuário, total de tasks)] com as contagens numa única consulta."""
        counts = self.tasks.count_by_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in self.users.list_page(limit, offset)]

    def get_user(self, user_id):
        user = self.users.find_by_id(user_id)
        if user is None:
            raise AppError(USER_NOT_FOUND, status=404)
        return user

    def list_user_tasks(self, user_id, limit=None, offset=0):
        self.get_user(user_id)
        return self.tasks.find_by_user(user_id, limit, offset)

    def create_user(self, name, email, password, role, actor_is_admin):
        if self.users.find_by_email(email) is not None:
            raise AppError('Email já cadastrado', status=409)
        self._check_role_assignment(role, current_role=DEFAULT_ROLE, actor_is_admin=actor_is_admin)

        user = self.users(name=name, email=email, role=role)
        user.set_password(password)
        with persistence_failure('Erro ao criar usuário'):
            user.save()
        logger.info('Usuário criado: %s', user.id)
        return user

    def update_user(self, user_id, fields, actor_is_admin):
        user = self.get_user(user_id)
        if 'email' in fields:
            existing = self.users.find_by_email(fields['email'])
            if existing is not None and existing.id != user_id:
                raise AppError('Email já cadastrado', status=409)
        if 'role' in fields:
            self._check_role_assignment(fields['role'], current_role=user.role, actor_is_admin=actor_is_admin)

        for name in ('name', 'email', 'role', 'active'):
            if name in fields:
                setattr(user, name, fields[name])
        if 'password' in fields:
            user.set_password(fields['password'])

        with persistence_failure('Erro ao atualizar'):
            user.save()
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        with persistence_failure('Erro ao deletar'):
            user.delete_with_tasks()
        logger.info('Usuário deletado: %s', user_id)

    def login(self, email, password):
        user = self.users.find_by_email(email)
        if user is None or not user.check_password(password):
            raise AppError('Credenciais inválidas', status=401)
        if not user.active:
            raise AppError('Usuário inativo', status=403)
        if user.has_legacy_password_hash():
            self._upgrade_password_hash(user, password)
        return user, f'{TOKEN_PREFIX}{user.id}'

    @staticmethod
    def _check_role_assignment(role, current_role, actor_is_admin):
        """O próprio cliente não escolhe um papel privilegiado nem troca o papel de alguém."""
        if role != current_role and not actor_is_admin:
            raise AppError('Acesso administrativo negado', status=401)

    @staticmethod
    def _upgrade_password_hash(user, password):
        """Regrava hashes MD5 antigos no formato atual após um login bem-sucedido."""
        user.set_password(password)
        try:
            user.save()
        except PersistenceError:
            logger.warning('Não foi possível atualizar o hash de senha do usuário %s', user.id)
