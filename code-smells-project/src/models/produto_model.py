COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def _produto(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoModel:
    def __init__(self, conexao):
        self._conexao = conexao

    def listar(self, limite, deslocamento):
        rows = self._conexao().execute(
            f"SELECT {COLUNAS} FROM produtos ORDER BY id LIMIT ? OFFSET ?",
            (limite, deslocamento),
        ).fetchall()
        return [_produto(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._conexao().execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _produto(row) if row else None

    def buscar_por_ids(self, produto_ids):
        ids = list(produto_ids)
        if not ids:
            return {}
        marcadores = ", ".join("?" for _ in ids)
        rows = self._conexao().execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id IN ({marcadores})", ids
        ).fetchall()
        return {row["id"]: _produto(row) for row in rows}

    def buscar(self, termo, categoria, preco_min, preco_max, limite, deslocamento):
        clausulas, parametros = [], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            parametros.append(categoria)
        if preco_min:
            clausulas.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            clausulas.append("preco <= ?")
            parametros.append(preco_max)
        where = f" WHERE {' AND '.join(clausulas)}" if clausulas else ""
        rows = self._conexao().execute(
            f"SELECT {COLUNAS} FROM produtos{where} ORDER BY id LIMIT ? OFFSET ?",
            parametros + [limite, deslocamento],
        ).fetchall()
        return [_produto(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self._conexao()
        with conexao:
            conexao.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def excluir(self, produto_id):
        conexao = self._conexao()
        with conexao:
            conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
