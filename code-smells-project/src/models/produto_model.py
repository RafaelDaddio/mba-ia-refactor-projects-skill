"""Acesso a dados de produtos."""

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _para_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def listar(self, limite, offset):
        rows = self.db.conn.execute(
            "SELECT * FROM produtos ORDER BY id LIMIT ? OFFSET ?", (limite, offset)
        ).fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self.db.conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _para_dict(row) if row else None

    def buscar(self, limite, offset, termo=None, categoria=None, preco_min=None, preco_max=None):
        # Só cláusulas fixas entram no texto; os valores vão nos parâmetros.
        clausulas, params = [], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            params.append(preco_max)
        where = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        rows = self.db.conn.execute(
            f"SELECT * FROM produtos {where} ORDER BY id LIMIT ? OFFSET ?", (*params, limite, offset)
        ).fetchall()
        return [_para_dict(row) for row in rows]

    def inserir(self, nome, descricao, preco, estoque, categoria):
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
            return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def baixar_estoque(self, produto_id, quantidade):
        """Baixa condicional: devolve False se o estoque não cobre a quantidade."""
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (quantidade, produto_id, quantidade),
            )
            return cursor.rowcount > 0

    def devolver_estoque(self, produto_id, quantidade):
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id)
            )

    def contar(self):
        return self.db.conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
