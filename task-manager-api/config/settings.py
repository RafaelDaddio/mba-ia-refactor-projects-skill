"""Configuração da aplicação, lida do ambiente do processo."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)

# O Flask-SQLAlchemy resolve URIs SQLite relativas para a pasta instance/ na raiz do projeto.
DEFAULT_DATABASE_URI = 'sqlite:///tasks.db'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5000
DEFAULT_CORS_ORIGINS = 'http://localhost:3000'


def _as_bool(value, default=False):
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        # `or`: variável definida mas vazia vale como ausente
        self.debug = _as_bool(env.get('APP_DEBUG'))
        self.host = env.get('APP_HOST') or DEFAULT_HOST
        self.port = int(env.get('APP_PORT') or DEFAULT_PORT)
        self.database_uri = env.get('DATABASE_URI') or DEFAULT_DATABASE_URI
        self.secret_key = env.get('SECRET_KEY') or self._ephemeral_secret()
        self.admin_token = env.get('ADMIN_TOKEN') or None
        self.seed_admin_password = env.get('SEED_ADMIN_PASSWORD') or None
        self.cors_origins = [
            origin.strip()
            for origin in (env.get('CORS_ORIGINS') or DEFAULT_CORS_ORIGINS).split(',')
            if origin.strip()
        ]

    @staticmethod
    def _ephemeral_secret():
        logger.warning(
            'SECRET_KEY não definida: usando chave aleatória temporária; '
            'os tokens emitidos deixam de valer a cada reinício.'
        )
        return secrets.token_hex(32)
