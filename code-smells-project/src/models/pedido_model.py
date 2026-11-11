PRODUTO_DESCONHECIDO = "Desconhecido"


class EstoqueInsuficiente(Exception):
    """A baixa de estoque não encontrou unidades suficientes; a transação foi desfeita."""

    def __init__(self, produto_id):
        super().__init__(produto_id)
        self.produto_id = produto_id


def _pedido(row):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
    }


class PedidoModel:
    def __init__(self, conexao):
        self._conexao = conexao

    def listar(self, limite, deslocamento, usuario_id=None):
        """Pedidos com itens e nome do produto numa única consulta (sem N+1)."""
        rows = self._conexao().execute(
            """
            WITH selecionados AS (
                SELECT id, usuario_id, status, total, criado_em
                FROM pedidos
                WHERE (? IS NULL OR usuario_id = ?)
                ORDER BY id
                LIMIT ? OFFSET ?
            )
            SELECT s.id, s.usuario_id, s.status, s.total, s.criado_em,
                   i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
                   p.id AS produto_existe, p.nome AS produto_nome
            FROM selecionados s
            LEFT JOIN itens_pedido i ON i.pedido_id = s.id
            LEFT JOIN produtos p ON p.id = i.produto_id
            ORDER BY s.id, i.id
            """,
            (usuario_id, usuario_id, limite, deslocamento),
        ).fetchall()

        pedidos = {}
        for row in rows:
            pedido = pedidos.get(row["id"])
            if pedido is None:
                pedido = {**_pedido(row), "itens": []}
                pedidos[row["id"]] = pedido
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] if row["produto_existe"] is not None else PRODUTO_DESCONHECIDO,
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def buscar_por_id(self, pedido_id):
        row = self._conexao().execute(
            "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        return _pedido(row) if row else None

    def criar(self, usuario_id, status, total, itens):
        """Grava pedido, itens e baixa de estoque numa transação.

        `itens` é uma lista de (produto_id, quantidade, preco_unitario).
        Lança EstoqueInsuficiente (com rollback) se alguma baixa deixaria o estoque negativo.
        """
        conexao = self._conexao()
        with conexao:
            pedido_id = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, status, total),
            ).lastrowid
            for produto_id, quantidade, preco_unitario in itens:
                conexao.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, produto_id, quantidade, preco_unitario),
                )
                baixa = conexao.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (quantidade, produto_id, quantidade),
                )
                if baixa.rowcount == 0:
                    raise EstoqueInsuficiente(produto_id)
        return pedido_id

    def atualizar_status(self, pedido_id, status):
        conexao = self._conexao()
        with conexao:
            conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def cancelar_devolvendo_estoque(self, pedido_id, status_cancelado):
        """Muda o status para cancelado e devolve os itens ao estoque, uma única vez.

        Devolve False (sem alterar nada) se o pedido já estava cancelado.
        """
        conexao = self._conexao()
        with conexao:
            mudou = conexao.execute(
                "UPDATE pedidos SET status = ? WHERE id = ? AND (status IS NULL OR status <> ?)",
                (status_cancelado, pedido_id, status_cancelado),
            )
            if mudou.rowcount == 0:
                return False
            conexao.execute(
                """
                UPDATE produtos
                SET estoque = estoque + (
                    SELECT SUM(i.quantidade) FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )
        return True

    def resumo_por_status(self):
        rows = self._conexao().execute(
            "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS soma "
            "FROM pedidos GROUP BY status"
        ).fetchall()
        return [dict(row) for row in rows]

    def contar(self):
        return self._conexao().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
