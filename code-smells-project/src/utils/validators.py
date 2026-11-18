"""Validadores genéricos de entrada (corpo JSON e query string)."""
import math

from src.utils.errors import AppError

LIMITE_PADRAO = 100
LIMITE_MAXIMO = 500


def corpo_json(request, obrigatorio=True):
    """Corpo da requisição como objeto JSON.

    Com `obrigatorio=False`, corpo ausente ou vazio vira `{}` e cada campo é
    validado por quem chama.
    """
    dados = request.get_json(silent=True)
    if dados is None and not obrigatorio:
        return {}
    if not isinstance(dados, dict) or (obrigatorio and not dados):
        raise AppError("Dados inválidos", status=400)
    return dados


def exigir_texto(valor, mensagem):
    if not isinstance(valor, str):
        raise AppError(mensagem, status=400)
    return valor


def exigir_numero(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise AppError(mensagem, status=400)
    return valor


def exigir_inteiro(valor, mensagem, minimo=None):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise AppError(mensagem, status=400)
    if minimo is not None and valor < minimo:
        raise AppError(mensagem, status=400)
    return valor


def query_float(args, campo):
    bruto = args.get(campo)
    if bruto in (None, ""):
        return None
    try:
        valor = float(bruto)
    except ValueError:
        valor = math.nan
    if not math.isfinite(valor):
        raise AppError(f"'{campo}' deve ser numérico", status=400)
    return valor


def query_int(args, campo, padrao=None):
    bruto = args.get(campo)
    if bruto in (None, ""):
        return padrao
    try:
        return int(bruto)
    except ValueError:
        raise AppError(f"'{campo}' deve ser um número inteiro", status=400) from None


def paginacao(args):
    """Lê `limite` e `offset` opcionais da query string."""
    limite = query_int(args, "limite", LIMITE_PADRAO)
    offset = query_int(args, "offset", 0)
    if limite < 1 or offset < 0:
        raise AppError("Parâmetros de paginação inválidos", status=400)
    return min(limite, LIMITE_MAXIMO), offset
