"""Acesso a dados de usuários."""
import sqlite3

from src.models.base_model import BaseModel

# A senha (hash) nunca entra na representação pública do usuário.
_COLUNAS_PUBLICAS = ("id", "nome", "email", "tipo", "criado_em")
_SELECT = f"SELECT {', '.join(_COLUNAS_PUBLICAS)} FROM usuarios"


def _para_dict(linha):
    return {coluna: linha[coluna] for coluna in _COLUNAS_PUBLICAS}


class UsuarioModel(BaseModel):
    def listar(self, limite, offset):
        linhas = self._conn.execute(
            f"{_SELECT} ORDER BY id LIMIT ? OFFSET ?", (limite, offset)
        ).fetchall()
        return [_para_dict(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        linha = self._conn.execute(f"{_SELECT} WHERE id = ?", (usuario_id,)).fetchone()
        return _para_dict(linha) if linha else None

    def email_existe(self, email):
        linha = self._conn.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone()
        return linha is not None

    def listar_credenciais_por_email(self, email):
        """Uso interno da autenticação: inclui o hash da senha.

        Devolve uma lista porque bancos antigos podem ter e-mails duplicados.
        """
        linhas = self._conn.execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id",
            (email,),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def criar(self, nome, email, senha_hash):
        """Insere o usuário e devolve o id, ou None se o e-mail já existe."""
        try:
            cursor = self._conn.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, senha_hash),
            )
        except sqlite3.IntegrityError:
            return None
        return cursor.lastrowid
