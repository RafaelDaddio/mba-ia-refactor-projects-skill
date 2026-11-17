"""Dados de exemplo do primeiro boot (controlado por SEED_ON_START)."""
import logging
import secrets

from src.utils.senhas import gerar_hash

logger = logging.getLogger(__name__)

EMAIL_ADMIN = "admin@loja.com"

PRODUTOS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Contas de cliente de demonstração; a senha do administrador vem da configuração.
CLIENTES = [
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
]


def _vazia(conn, tabela):
    return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] == 0


def popular_se_vazio(db, senha_admin=None):
    """Insere os dados de exemplo em cada tabela que estiver vazia."""
    with db.transaction() as conn:
        if _vazia(conn, "produtos"):
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                PRODUTOS,
            )
        if _vazia(conn, "usuarios"):
            if senha_admin is None:
                senha_admin = secrets.token_urlsafe(16)
                logger.warning(
                    "SEED_ADMIN_PASSWORD não definida: %s criado com senha aleatória. "
                    "Use o ADMIN_TOKEN ou defina a variável antes do primeiro boot.",
                    EMAIL_ADMIN,
                )
            usuarios = [("Admin", EMAIL_ADMIN, gerar_hash(senha_admin), "admin")]
            usuarios += [(nome, email, gerar_hash(senha), "cliente") for nome, email, senha in CLIENTES]
            conn.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                usuarios,
            )
