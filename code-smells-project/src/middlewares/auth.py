import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import AppError

HEADER_TOKEN_ADMIN = "X-Admin-Token"


def exigir_admin(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, nega sempre."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = (current_app.config.get("ADMIN_TOKEN") or "").encode()
        informado = (request.headers.get(HEADER_TOKEN_ADMIN) or "").encode()
        if not esperado or not hmac.compare_digest(informado, esperado):
            raise AppError("Acesso administrativo negado", status=401)
        return view(*args, **kwargs)

    return wrapper


def exigir_recurso_habilitado(chave_config):
    """Bloqueia (403) o endpoint enquanto a flag de configuração estiver desligada."""

    def decorador(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_app.config.get(chave_config):
                raise AppError("Endpoint desabilitado", status=403)
            return view(*args, **kwargs)

        return wrapper

    return decorador
