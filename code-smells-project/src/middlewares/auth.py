"""Autenticação e níveis de acesso: pública, conta autenticada, dono da conta e administrador."""
import hmac
from functools import wraps

from flask import request
from itsdangerous import BadData, URLSafeTimedSerializer

from src.utils.errors import AppError

VALIDADE_TOKEN = 8 * 3600  # segundos
_PREFIXO = "Bearer "


class Auth:
    def __init__(self, secret_key, admin_token=None):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._admin_token = (admin_token or "").encode()

    def issue_token(self, usuario_id, is_admin=False):
        """Token assinado com o id e o papel da conta; o papel vale até o token expirar."""
        return self._serializer.dumps({"uid": usuario_id, "adm": bool(is_admin)})

    def _claims(self):
        """Conteúdo do token Bearer; None se ausente, adulterado ou expirado."""
        header = request.headers.get("Authorization", "")
        if not header.startswith(_PREFIXO):
            return None
        try:
            claims = self._serializer.loads(header[len(_PREFIXO):], max_age=VALIDADE_TOKEN)
        except BadData:
            return None
        return claims if isinstance(claims, dict) and "uid" in claims else None

    def _admin_token_ok(self):
        informado = request.headers.get("X-Admin-Token", "").encode()
        return bool(self._admin_token) and hmac.compare_digest(informado, self._admin_token)

    def is_admin(self):
        claims = self._claims()
        return self._admin_token_ok() or bool(claims and claims.get("adm"))

    def require_user(self):
        """Nível "conta autenticada". Devolve o id da conta (None para o token administrativo)."""
        if self._admin_token_ok():
            return None
        claims = self._claims()
        if claims is None:
            raise AppError("Autenticação necessária", status=401)
        return claims["uid"]

    def require_account_owner(self, usuario_id):
        """Nível "dono da conta ou administrador"."""
        if self.is_admin():
            return
        if self.require_user() != usuario_id:
            raise AppError("Acesso negado a esta conta", status=403)

    def require_admin(self):
        """Nível "administrador"."""
        if self.is_admin():
            return
        self.require_user()  # 401 sem credencial
        raise AppError("Acesso restrito a administradores", status=403)

    def user_only(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            self.require_user()
            return view(*args, **kwargs)
        return wrapper

    def admin_only(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            self.require_admin()
            return view(*args, **kwargs)
        return wrapper
