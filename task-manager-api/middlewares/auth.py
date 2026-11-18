"""Autenticação por token assinado e níveis de acesso das rotas."""
import hmac
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadData, URLSafeTimedSerializer

from utils.errors import AppError

TOKEN_MAX_AGE = 8 * 3600  # segundos
TOKEN_SALT = 'auth-token'
ACCOUNT_LOADER_KEY = 'auth_load_account'


def init_auth(app, load_account):
    """Chamada na composition root. load_account(user_id) devolve {"id", "is_admin"}
    da conta atual, ou None se ela não existe ou não passaria no login (ex.: inativa)."""
    app.extensions[ACCOUNT_LOADER_KEY] = load_account


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)


def issue_token(user_id):
    """O token só identifica a conta; papel e situação são lidos a cada requisição."""
    return _serializer().dumps({'uid': user_id})


def _current_account():
    """Conta do token Bearer, recarregada uma vez por requisição; None se não houver conta válida."""
    if 'auth_account' not in g:
        g.auth_account = None
        header = request.headers.get('Authorization', '')
        if header.startswith('Bearer '):
            try:
                claims = _serializer().loads(header[len('Bearer '):], max_age=TOKEN_MAX_AGE)
            except BadData:
                claims = None
            if isinstance(claims, dict) and isinstance(claims.get('uid'), int):
                g.auth_account = current_app.extensions[ACCOUNT_LOADER_KEY](claims['uid'])
    return g.auth_account


def _admin_token_ok():
    expected = (current_app.config.get('ADMIN_TOKEN') or '').encode()
    provided = request.headers.get('X-Admin-Token', '').encode()
    return bool(expected) and hmac.compare_digest(provided, expected)


def is_admin():
    account = _current_account()
    return _admin_token_ok() or bool(account and account['is_admin'])


def require_user():
    """Nível "conta autenticada". Devolve o id da conta (None para o token administrativo)."""
    if _admin_token_ok():
        return None
    account = _current_account()
    if account is None:
        raise AppError('Autenticação necessária', status=401)
    return account['id']


def require_account_owner(user_id):
    """Nível "dono da conta ou administrador"."""
    if is_admin():
        return
    if require_user() != user_id:
        raise AppError('Acesso negado a esta conta', status=403)


def require_admin():
    """Nível "administrador"."""
    if is_admin():
        return
    require_user()  # 401 sem credencial
    raise AppError('Acesso restrito a administradores', status=403)


def user_only(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_user()
        return view(*args, **kwargs)
    return wrapper


def owner_only(view):
    """Para rotas com `<int:user_id>` no caminho: a conta do caminho ou um administrador."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_account_owner(kwargs['user_id'])
        return view(*args, **kwargs)
    return wrapper


def admin_only(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_admin()
        return view(*args, **kwargs)
    return wrapper
