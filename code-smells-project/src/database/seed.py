"""Dados de exemplo inseridos quando o banco está vazio (primeiro boot)."""
import logging
import secrets

from src.utils.senhas import gerar_hash

logger = logging.getLogger(__name__)

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

ADMIN = ("Admin", "admin@loja.com", "admin")

# Contas comuns de exemplo: (nome, email, senha, tipo)
CLIENTES = [
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def popular_se_vazio(conn, senha_admin=None):
    """Insere os dados de exemplo se a tabela de produtos estiver vazia."""
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return

    with conn:
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS,
        )
        nome, email, tipo = ADMIN
        if not _email_existe(conn, email):
            if senha_admin is None:
                senha_admin = secrets.token_urlsafe(16)
                logger.warning(
                    "SEED_ADMIN_PASSWORD não definida: a conta %s foi criada com senha aleatória. "
                    "Use o X-Admin-Token ou defina a variável antes do primeiro boot.",
                    email,
                )
            _inserir_usuario(conn, nome, email, senha_admin, tipo)
        for nome, email, senha, tipo in CLIENTES:
            if not _email_existe(conn, email):
                _inserir_usuario(conn, nome, email, senha, tipo)
    logger.info("Banco populado com os dados de exemplo.")


def _email_existe(conn, email):
    return conn.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def _inserir_usuario(conn, nome, email, senha, tipo):
    conn.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, gerar_hash(senha), tipo),
    )
