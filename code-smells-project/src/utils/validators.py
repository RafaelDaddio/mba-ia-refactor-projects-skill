"""Validadores genéricos de entrada. Lançam AppError (400) com a mensagem para o cliente."""
import math

from src.utils.errors import AppError

MENSAGEM_DADOS_INVALIDOS = "Dados inválidos"
LIMITE_PADRAO = 100
LIMITE_MAXIMO = 500


def exigir_objeto(dados, permitir_vazio=False):
    """Corpo JSON precisa ser um objeto; por padrão, um objeto vazio também é recusado."""
    if not isinstance(dados, dict) or (not dados and not permitir_vazio):
        raise AppError(MENSAGEM_DADOS_INVALIDOS)
    return dados


def eh_numero(valor):
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and math.isfinite(valor)
    )


def como_inteiro(valor):
    """Inteiro recebido como número (5 ou 5.0); None para qualquer outro valor."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and math.isfinite(valor) and valor.is_integer():
        return int(valor)
    return None


def como_id(valor):
    """Identificador inteiro positivo, aceito como número ou texto de dígitos; None se inválido."""
    if isinstance(valor, str) and valor.strip().isdigit():
        valor = int(valor.strip())
    inteiro = como_inteiro(valor)
    return inteiro if inteiro is not None and inteiro >= 1 else None


def numero_opcional(bruto, campo):
    """Número opcional vindo da query string."""
    if bruto in (None, ""):
        return None
    try:
        valor = float(bruto)
    except ValueError:
        raise AppError(f"'{campo}' deve ser numérico") from None
    if not math.isfinite(valor):
        raise AppError(f"'{campo}' deve ser numérico")
    return valor


def _inteiro_da_query(bruto, campo, padrao):
    if bruto in (None, ""):
        return padrao
    try:
        return int(bruto)
    except ValueError:
        raise AppError(f"'{campo}' deve ser um número inteiro") from None


def paginacao(limit_bruto, offset_bruto):
    """Paginação opcional (`limit`, `offset`); o padrão cobre as listagens atuais."""
    limite = _inteiro_da_query(limit_bruto, "limit", LIMITE_PADRAO)
    deslocamento = _inteiro_da_query(offset_bruto, "offset", 0)
    if limite < 1 or deslocamento < 0:
        raise AppError("Parâmetros de paginação inválidos")
    return min(limite, LIMITE_MAXIMO), deslocamento
