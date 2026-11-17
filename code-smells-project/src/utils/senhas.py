"""Hash de senha com salt (Werkzeug, já instalado com o Flask)."""
from werkzeug.security import check_password_hash, generate_password_hash


def gerar_hash(senha):
    return generate_password_hash(senha)


def conferir(senha_hash, senha):
    """False também para valores que não são hash (ex.: senha antiga em texto puro)."""
    return check_password_hash(senha_hash, senha)
