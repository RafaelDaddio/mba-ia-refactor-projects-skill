"""Autenticação e níveis de acesso.

Provas aceitas:
- token de usuário (`Authorization: Bearer <token>`), emitido pelo login. O token só
  identifica a conta: a cada requisição ela é recarregada, precisa existir e vale o
  papel atual dela;
- token administrativo (`X-Admin-Token`), definido na configuração.

Níveis: pública (sem verificação), conta autenticada, dono da conta ou administrador,
e administrador. Sem prova, 401; prova insuficiente, 403.
"""
import hmac
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadData, URLSafeTimedSerializer

from src.utils.errors import AppError

TOKEN_VALIDADE_SEGUNDOS = 8 * 3600
_PREFIXO_BEARER = "Bearer "


def init_auth(app, carregar_conta):
    """Chamada na composition root.

    `carregar_conta(usuario_id)` devolve {"id", "is_admin"} da conta atual, ou None
    se ela não existe mais.
    """
    app.extensions["auth_carregar_conta"] = carregar_conta


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth-token")


def emitir_token(usuario_id):
    return _serializer().dumps({"uid": usuario_id})


def _conta_atual():
    """Conta do token Bearer, recarregada uma vez por requisição; None se não houver conta válida."""
    if "auth_conta" not in g:
        g.auth_conta = None
        header = request.headers.get("Authorization", "")
        if header.startswith(_PREFIXO_BEARER):
            try:
                claims = _serializer().loads(
                    header[len(_PREFIXO_BEARER):], max_age=TOKEN_VALIDADE_SEGUNDOS
                )
            except BadData:
                claims = None
            if isinstance(claims, dict) and isinstance(claims.get("uid"), int):
                g.auth_conta = current_app.extensions["auth_carregar_conta"](claims["uid"])
    return g.auth_conta


def _token_admin_ok():
    esperado = (current_app.config.get("ADMIN_TOKEN") or "").encode()
    recebido = request.headers.get("X-Admin-Token", "").encode()
    return bool(esperado) and hmac.compare_digest(recebido, esperado)


def eh_admin():
    conta = _conta_atual()
    return _token_admin_ok() or bool(conta and conta["is_admin"])


def exigir_usuario():
    """Nível "conta autenticada". Devolve o id da conta (None para o token administrativo)."""
    if _token_admin_ok():
        return None
    conta = _conta_atual()
    if conta is None:
        raise AppError("Autenticação necessária", status=401)
    return conta["id"]


def exigir_dono(usuario_id):
    """Nível "dono da conta ou administrador"."""
    if eh_admin():
        return
    if exigir_usuario() != usuario_id:
        raise AppError("Acesso negado a esta conta", status=403)


def exigir_admin():
    """Nível "administrador"."""
    if eh_admin():
        return
    exigir_usuario()  # 401 sem credencial
    raise AppError("Acesso restrito a administradores", status=403)


def somente_autenticado(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        exigir_usuario()
        return view(*args, **kwargs)
    return wrapper


def somente_dono(parametro):
    """Para rotas em que a conta vem do caminho (ex.: `/usuarios/<int:usuario_id>`)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            exigir_dono(kwargs[parametro])
            return view(*args, **kwargs)
        return wrapper
    return decorator


def somente_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        exigir_admin()
        return view(*args, **kwargs)
    return wrapper
