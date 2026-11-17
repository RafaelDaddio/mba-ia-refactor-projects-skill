"""Validadores genéricos de entrada (tipo, faixa e formato), sem regra de domínio."""
import math

from src.utils.errors import AppError

LIMITE_PADRAO = 100
LIMITE_MAXIMO = 500


def objeto_json(dados, permitir_vazio=False):
    """Garante que o corpo da requisição é um objeto JSON."""
    if not isinstance(dados, dict) or (not dados and not permitir_vazio):
        raise AppError("Dados inválidos")
    return dados


def texto(valor, mensagem):
    if not isinstance(valor, str):
        raise AppError(mensagem)
    return valor


def numero(valor, mensagem):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise AppError(mensagem)
    return valor


def inteiro(valor, mensagem, minimo=None):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise AppError(mensagem)
    if minimo is not None and valor < minimo:
        raise AppError(mensagem)
    return valor


def query_float(args, campo):
    """Número da query string; None quando ausente ou vazio."""
    bruto = args.get(campo)
    if not bruto:
        return None
    try:
        valor = float(bruto)
    except ValueError:
        valor = math.nan
    if not math.isfinite(valor):
        raise AppError(f"'{campo}' deve ser numérico")
    return valor


def _query_int(args, campo, padrao):
    bruto = args.get(campo)
    if not bruto:
        return padrao
    try:
        return int(bruto)
    except ValueError:
        raise AppError(f"'{campo}' deve ser um número inteiro") from None


def paginacao(args):
    """`limit` e `offset` opcionais; sem eles, vale o limite padrão."""
    limite = _query_int(args, "limit", LIMITE_PADRAO)
    offset = _query_int(args, "offset", 0)
    if limite < 1 or offset < 0:
        raise AppError("Parâmetros de paginação inválidos")
    return min(limite, LIMITE_MAXIMO), offset
