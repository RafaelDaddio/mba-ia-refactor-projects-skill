"""Hash de senhas com o Werkzeug (salt aleatório por senha)."""
from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_DE_HASH = ("scrypt:", "pbkdf2:")


def gerar_hash(senha):
    return generate_password_hash(senha)


def conferir_senha(hash_gravado, senha):
    return check_password_hash(hash_gravado, senha)


def eh_hash(valor):
    """Indica se o valor gravado já é um hash gerado por `gerar_hash`."""
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_DE_HASH)
