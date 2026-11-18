"""Banco de dados: conexão por requisição, schema e seed explícitos."""
from src.database.connection import close_db, get_db
from src.database.schema import criar_schema
from src.database.seed import popular_se_vazio

__all__ = ["get_db", "init_db"]


def init_db(app, seed=True, senha_admin_seed=None):
    """Registra o fechamento da conexão e prepara o banco na inicialização."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        criar_schema(conn)
        if seed:
            popular_se_vazio(conn, senha_admin_seed)
