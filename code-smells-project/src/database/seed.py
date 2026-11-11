"""Dados de exemplo para desenvolvimento, inseridos só quando não há produtos."""
import logging

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

PRODUTOS_EXEMPLO = (
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
)

# Credenciais de exemplo, só para desenvolvimento. Fora dele, defina
# SEED_ADMIN_PASSWORD ou desligue o seed com SEED_ON_START=false.
SENHA_ADMIN_EXEMPLO = "admin123"
CLIENTES_EXEMPLO = (
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
)


def popular_se_vazio(conexao, senha_admin=None):
    if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return

    if senha_admin is None:
        senha_admin = SENHA_ADMIN_EXEMPLO
        logger.warning(
            "Seed: admin@loja.com criado com a senha de exemplo; "
            "defina SEED_ADMIN_PASSWORD ou SEED_ON_START=false fora do desenvolvimento."
        )

    usuarios = [("Admin", "admin@loja.com", generate_password_hash(senha_admin), "admin")]
    usuarios += [
        (nome, email, generate_password_hash(senha), "cliente")
        for nome, email, senha in CLIENTES_EXEMPLO
    ]

    with conexao:
        conexao.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_EXEMPLO,
        )
        conexao.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            usuarios,
        )
    logger.info("Banco populado com dados de exemplo.")
