"""Acesso a dados de usuários. O campo `senha` guarda o hash e não sai da camada de serviço."""

_CAMPOS = ("id", "nome", "email", "senha", "tipo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


class UsuarioModel:
    def __init__(self, db):
        self.db = db

    def listar(self, limite, offset):
        rows = self.db.conn.execute(
            "SELECT * FROM usuarios ORDER BY id LIMIT ? OFFSET ?", (limite, offset)
        ).fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self.db.conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _para_dict(row) if row else None

    def buscar_por_email(self, email):
        row = self.db.conn.execute(
            "SELECT * FROM usuarios WHERE email = ? ORDER BY id LIMIT 1", (email,)
        ).fetchone()
        return _para_dict(row) if row else None

    def inserir(self, nome, email, senha_hash, tipo):
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
            return cursor.lastrowid

    def contar(self):
        return self.db.conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
