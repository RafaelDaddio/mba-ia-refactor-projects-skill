"""Acesso a dados de produtos."""
from src.models.base_model import BaseModel

_COLUNAS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
_SELECT = f"SELECT {', '.join(_COLUNAS)} FROM produtos"


def _para_dict(linha):
    return {coluna: linha[coluna] for coluna in _COLUNAS}


class ProdutoModel(BaseModel):
    def listar(self, limite, offset):
        linhas = self._conn.execute(
            f"{_SELECT} ORDER BY id LIMIT ? OFFSET ?", (limite, offset)
        ).fetchall()
        return [_para_dict(linha) for linha in linhas]

    def buscar_por_id(self, produto_id):
        linha = self._conn.execute(f"{_SELECT} WHERE id = ?", (produto_id,)).fetchone()
        return _para_dict(linha) if linha else None

    def buscar(self, termo, categoria, preco_min, preco_max, limite, offset):
        # Só cláusulas fixas entram no texto do SQL; os valores vão nos parâmetros.
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
        linhas = self._conn.execute(
            f"{_SELECT}{where} ORDER BY id LIMIT ? OFFSET ?", (*parametros, limite, offset)
        ).fetchall()
        return [_para_dict(linha) for linha in linhas]

    def criar(self, nome, descricao, preco, estoque, categoria):
        cursor = self._conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        """Devolve False se o produto não existe."""
        cursor = self._conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        return cursor.rowcount == 1

    def deletar(self, produto_id):
        """Devolve False se o produto não existe."""
        cursor = self._conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        return cursor.rowcount == 1

    def baixar_estoque(self, produto_id, quantidade):
        """Baixa condicional: só altera se houver estoque. Devolve False se não baixou."""
        cursor = self._conn.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount == 1

    def devolver_estoque(self, produto_id, quantidade):
        self._conn.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id)
        )
