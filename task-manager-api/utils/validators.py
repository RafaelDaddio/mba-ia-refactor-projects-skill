"""Validação de formato da entrada, usada pelos controllers."""
from utils.errors import AppError

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
INVALID_BODY_MESSAGE = 'Dados inválidos'


def json_body(request, allow_empty=False):
    """Corpo JSON como objeto. JSON malformado ou content-type errado seguem como erro HTTP do framework."""
    data = request.get_json()
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise AppError(INVALID_BODY_MESSAGE, status=400)
    return data


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def optional_str(value, message):
    if value is not None and not isinstance(value, str):
        raise AppError(message, status=400)
    return value


def optional_id(value, message):
    """`None` significa "sem vínculo"; qualquer outro valor precisa ser um id inteiro."""
    if value is None:
        return None
    if not is_int(value):
        raise AppError(message, status=400)
    return value


def query_int(args, field, default=None):
    raw = args.get(field)
    if raw in (None, ''):
        return default
    try:
        return int(raw)
    except ValueError:
        raise AppError(f"Parâmetro '{field}' deve ser um número inteiro", status=400) from None


def pagination(args):
    limit = query_int(args, 'limit', DEFAULT_LIMIT)
    offset = query_int(args, 'offset', 0)
    if limit < 1 or offset < 0:
        raise AppError('Parâmetros de paginação inválidos', status=400)
    return min(limit, MAX_LIMIT), offset
