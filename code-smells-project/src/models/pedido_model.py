"""Acesso a dados de pedidos e seus itens."""

PRODUTO_DESCONHECIDO = "Desconhecido"  # nome devolvido quando o produto do item foi excluído


class PedidoModel:
    def __init__(self, db):
        self.db = db

    def inserir(self, usuario_id, status, total):
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, status, total),
            )
            return cursor.lastrowid

    def inserir_item(self, pedido_id, produto_id, quantidade, preco_unitario):
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, produto_id, quantidade, preco_unitario),
            )

    def buscar_por_id(self, pedido_id):
        row = self.db.conn.execute(
            "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        return dict(row) if row else None

    def quantidades_por_produto(self, pedido_id):
        """Pares (produto_id, quantidade total) dos itens de um pedido."""
        rows = self.db.conn.execute(
            "SELECT produto_id, SUM(quantidade) AS quantidade FROM itens_pedido "
            "WHERE pedido_id = ? GROUP BY produto_id ORDER BY produto_id",
            (pedido_id,),
        ).fetchall()
        return [(row["produto_id"], row["quantidade"]) for row in rows]

    def listar(self, limite, offset, usuario_id=None):
        """Pedidos com itens em duas queries: a página de pedidos e os itens dela."""
        conn = self.db.conn
        where, params = ("WHERE usuario_id = ?", [usuario_id]) if usuario_id is not None else ("", [])
        rows = conn.execute(
            f"SELECT id, usuario_id, status, total, criado_em FROM pedidos {where} "
            "ORDER BY id LIMIT ? OFFSET ?",
            (*params, limite, offset),
        ).fetchall()
        pedidos = {row["id"]: {**dict(row), "itens": []} for row in rows}
        if not pedidos:
            return []

        marcadores = ", ".join("?" * len(pedidos))
        itens = conn.execute(
            "SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome "
            "FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id "
            f"WHERE i.pedido_id IN ({marcadores}) ORDER BY i.id",
            list(pedidos),
        ).fetchall()
        for item in itens:
            pedidos[item["pedido_id"]]["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] or PRODUTO_DESCONHECIDO,
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return list(pedidos.values())

    def atualizar_status(self, pedido_id, status):
        with self.db.transaction() as conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def resumo_por_status(self):
        """Quantidade e soma dos totais por status, numa única agregação."""
        rows = self.db.conn.execute(
            "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS total "
            "FROM pedidos GROUP BY status"
        ).fetchall()
        return {row["status"]: {"quantidade": row["quantidade"], "total": row["total"]} for row in rows}

    def contar(self):
        return self.db.conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
