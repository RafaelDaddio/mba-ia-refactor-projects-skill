def _usuario_publico(row):
    """Serialização única de usuário: a senha nunca sai do model."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UsuarioModel:
    def __init__(self, conexao):
        self._conexao = conexao

    def listar(self, limite, deslocamento):
        rows = self._conexao().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios ORDER BY id LIMIT ? OFFSET ?",
            (limite, deslocamento),
        ).fetchall()
        return [_usuario_publico(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._conexao().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _usuario_publico(row) if row else None

    def listar_credenciais_por_email(self, email):
        """Registros com o hash da senha, para uso exclusivo da autenticação."""
        rows = self._conexao().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id",
            (email,),
        ).fetchall()
        return [dict(row) for row in rows]

    def email_cadastrado(self, email):
        row = self._conexao().execute(
            "SELECT 1 FROM usuarios WHERE email = ? LIMIT 1", (email,)
        ).fetchone()
        return row is not None

    def criar(self, nome, email, senha_hash, tipo):
        conexao = self._conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
