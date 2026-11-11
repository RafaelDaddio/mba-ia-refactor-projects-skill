"""Validadores genéricos de entrada; lançam AppError (400)."""
import re

from utils.errors import AppError

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
DEFAULT_LIMIT = 100
MAX_LIMIT = 500


def require_object(data):
    """O corpo precisa ser um objeto JSON não vazio."""
    if not data or not isinstance(data, dict):
        raise AppError('Dados inválidos')
    return data


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_valid_email(value):
    return isinstance(value, str) and EMAIL_PATTERN.match(value) is not None


def optional_text(value, message):
    """Aceita texto ou None."""
    if value is not None and not isinstance(value, str):
        raise AppError(message)
    return value


def query_int(args, field, default=None):
    raw = args.get(field)
    if raw in (None, ''):
        return default
    try:
        return int(raw)
    except ValueError:
        raise AppError(f"'{field}' deve ser um número inteiro") from None


def pagination(args):
    """(limit, offset) da query string; sem parâmetros, devolve até DEFAULT_LIMIT registros."""
    limit = query_int(args, 'limit', DEFAULT_LIMIT)
    offset = query_int(args, 'offset', 0)
    if limit < 1 or offset < 0:
        raise AppError('Parâmetros de paginação inválidos')
    return min(limit, MAX_LIMIT), offset
