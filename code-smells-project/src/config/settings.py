"""Configuração da aplicação, lida das variáveis de ambiente do processo."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do projeto
VERSAO_API = "1.0.0"

_VERDADEIROS = {"1", "true", "yes", "on", "sim"}


def _as_bool(value, default=False):
    if value is None or not value.strip():
        return default
    return value.strip().lower() in _VERDADEIROS


def _resolver_caminho(value, default):
    """Caminhos relativos partem da raiz do projeto, não do diretório de execução."""
    if not value:
        return str(default)
    caminho = Path(value)
    return str(caminho if caminho.is_absolute() else BASE_DIR / caminho)


class Settings:
    """Variável definida mas vazia vale como ausente (usa o padrão)."""

    def __init__(self, env=None):
        env = os.environ if env is None else env

        self.debug = _as_bool(env.get("APP_DEBUG"))
        self.host = env.get("APP_HOST") or "127.0.0.1"
        self.port = int(env.get("APP_PORT") or "5000")
        self.database_path = _resolver_caminho(env.get("DATABASE_PATH"), BASE_DIR / "loja.db")
        self.seed_on_start = _as_bool(env.get("SEED_ON_START"), default=True)
        self.allow_admin_sql = _as_bool(env.get("ALLOW_ADMIN_SQL"))
        self.cors_origins = [
            origem.strip()
            for origem in (env.get("CORS_ORIGINS") or "").split(",")
            if origem.strip()
        ]

        # Segredos: sem valor padrão no código.
        self.secret_key = env.get("SECRET_KEY") or None
        self.secret_key_temporaria = self.secret_key is None
        if self.secret_key_temporaria:
            self.secret_key = secrets.token_hex(32)
        self.admin_token = env.get("ADMIN_TOKEN") or None
        self.seed_admin_password = env.get("SEED_ADMIN_PASSWORD") or None
