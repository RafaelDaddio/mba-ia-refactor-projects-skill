import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do projeto
VERSAO_API = "1.0.0"


def _texto(env, nome):
    """Valor da variável sem espaços; definida mas vazia vale como ausente."""
    valor = env.get(nome)
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


def _booleano(env, nome, padrao=False):
    valor = _texto(env, nome)
    if valor is None:
        return padrao
    return valor.lower() in {"1", "true", "yes", "on", "sim"}


def _inteiro(env, nome, padrao):
    valor = _texto(env, nome)
    if valor is None:
        return padrao
    try:
        return int(valor)
    except ValueError:
        raise ValueError(f"{nome} deve ser um número inteiro") from None


def _caminho_do_projeto(valor):
    caminho = Path(valor)
    return str(caminho if caminho.is_absolute() else BASE_DIR / caminho)


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env

        self.debug = _booleano(env, "APP_DEBUG")
        self.host = _texto(env, "APP_HOST") or "127.0.0.1"
        self.port = _inteiro(env, "APP_PORT", 5000)
        self.database_path = _caminho_do_projeto(_texto(env, "DATABASE_PATH") or "loja.db")
        self.seed_on_start = _booleano(env, "SEED_ON_START", padrao=True)
        self.seed_admin_password = _texto(env, "SEED_ADMIN_PASSWORD")

        segredo = _texto(env, "SECRET_KEY")
        self.secret_key_temporaria = segredo is None
        self.secret_key = segredo or secrets.token_hex(32)

        self.admin_token = _texto(env, "ADMIN_TOKEN")
        self.allow_admin_sql = _booleano(env, "ALLOW_ADMIN_SQL")

        origens = _texto(env, "CORS_ORIGINS") or "http://localhost:3000"
        self.cors_origins = [origem.strip() for origem in origens.split(",") if origem.strip()]

        self.versao_api = VERSAO_API
