"""Credencial administrativa por header (ADMIN_TOKEN da configuração)."""
import hmac

from flask import current_app, request

ADMIN_TOKEN_HEADER = 'X-Admin-Token'


def is_admin_request():
    """True quando a requisição traz o token administrativo configurado."""
    expected = current_app.config.get('ADMIN_TOKEN') or ''
    provided = request.headers.get(ADMIN_TOKEN_HEADER, '')
    return bool(expected) and hmac.compare_digest(provided.encode(), expected.encode())
