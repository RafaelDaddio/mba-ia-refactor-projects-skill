"""Configurações da aplicação.

Tudo que varia por ambiente é lido das variáveis de ambiente do processo
(documentadas em `.env.example`). Variável definida mas vazia vale como ausente.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do projeto

_VERDADEIROS = {"1", "true", "yes", "on", "sim"}


def _as_bool(value, default=False):
    if value is None or not value.strip():
        return default
    return value.strip().lower() in _VERDADEIROS


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env

        self.debug = _as_bool(env.get("APP_DEBUG"))
        self.host = env.get("APP_HOST") or "127.0.0.1"
        self.port = int(env.get("APP_PORT") or "5000")

        self.database_path = env.get("DATABASE_PATH") or str(BASE_DIR / "loja.db")
        self.seed_on_start = _as_bool(env.get("SEED_ON_START"), default=True)
        self.seed_admin_password = env.get("SEED_ADMIN_PASSWORD") or None

        # Segredos não têm valor padrão no código. Sem SECRET_KEY, usa-se uma chave
        # aleatória que só vale até o processo reiniciar (a composition root avisa no log).
        self.secret_key = env.get("SECRET_KEY") or None
        self.secret_key_is_ephemeral = self.secret_key is None
        if self.secret_key_is_ephemeral:
            self.secret_key = secrets.token_hex(32)

        self.admin_token = env.get("ADMIN_TOKEN") or None
        self.allow_admin_sql = _as_bool(env.get("ALLOW_ADMIN_SQL"))

        self.cors_origins = [
            origem.strip()
            for origem in (env.get("CORS_ORIGINS") or "http://localhost:3000").split(",")
            if origem.strip()
        ]
