"""Banco de dados: conexão, schema e seed, inicializados de forma explícita."""
from src.database.connection import Database
from src.database.schema import criar_schema
from src.database.seed import popular_se_vazio

__all__ = ["Database", "init_db"]


def init_db(app, db, seed=True, senha_admin=None):
    """Registra o fechamento da conexão, cria o schema e, se pedido, o seed."""
    app.teardown_appcontext(db.close)
    with app.app_context():
        criar_schema(db.conn)
        if seed:
            popular_se_vazio(db, senha_admin)
