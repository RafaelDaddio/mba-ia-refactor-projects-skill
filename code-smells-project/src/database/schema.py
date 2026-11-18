"""Schema do banco e ajustes aplicados a bancos já existentes."""
import logging
import sqlite3

from src.utils.senhas import eh_hash, gerar_hash

logger = logging.getLogger(__name__)

# `CREATE TABLE IF NOT EXISTS` não altera tabelas existentes: as restrições abaixo
# valem para bancos novos. As mesmas regras são verificadas nos services.
# `itens_pedido.produto_id` não tem chave estrangeira de propósito: excluir um
# produto com pedidos continua permitido, como antes.
SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    status TEXT DEFAULT 'pendente',
    total REAL NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL
);
"""


def criar_schema(conn):
    conn.executescript(SCHEMA)
    _migrar_senhas_em_texto_puro(conn)
    _criar_indice_unico_de_email(conn)


def _migrar_senhas_em_texto_puro(conn):
    """Bancos criados pela versão antiga guardavam a senha em texto puro."""
    pendentes = [
        (gerar_hash(str(linha["senha"])), linha["id"])
        for linha in conn.execute("SELECT id, senha FROM usuarios").fetchall()
        if linha["senha"] is not None and not eh_hash(linha["senha"])
    ]
    if not pendentes:
        return
    with conn:
        conn.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", pendentes)
    logger.warning("%d senha(s) em texto puro foram convertidas para hash.", len(pendentes))


def _criar_indice_unico_de_email(conn):
    try:
        with conn:
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)")
    except sqlite3.IntegrityError:
        logger.warning(
            "Há e-mails duplicados em 'usuarios': o índice único não foi criado. "
            "Novos cadastros duplicados continuam recusados pela aplicação."
        )
