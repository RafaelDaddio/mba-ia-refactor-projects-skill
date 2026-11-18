"""Acesso a dados de pedidos e seus itens."""
from src.models.base_model import BaseModel

PRODUTO_DESCONHECIDO = "Desconhecido"

# Os pedidos são paginados na subconsulta; os itens e o nome do produto vêm no
# mesmo SELECT, em vez de uma query por pedido e outra por item.
_LISTAR = """
SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
       i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
       pr.id AS produto_encontrado, pr.nome AS produto_nome
FROM (
    SELECT id, usuario_id, status, total, criado_em
    FROM pedidos
    WHERE (? IS NULL OR usuario_id = ?)
    ORDER BY id
    LIMIT ? OFFSET ?
) p
LEFT JOIN itens_pedido i ON i.pedido_id = p.id
LEFT JOIN produtos pr ON pr.id = i.produto_id
ORDER BY p.id, i.id
"""


class PedidoModel(BaseModel):
    def listar(self, limite, offset, usuario_id=None):
        linhas = self._conn.execute(_LISTAR, (usuario_id, usuario_id, limite, offset)).fetchall()
        pedidos = {}
        for linha in linhas:
            pedido = pedidos.setdefault(linha["id"], {
                "id": linha["id"],
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            })
            if linha["item_id"] is not None:
                produto_existe = linha["produto_encontrado"] is not None
                pedido["itens"].append({
                    "produto_id": linha["produto_id"],
                    "produto_nome": linha["produto_nome"] if produto_existe else PRODUTO_DESCONHECIDO,
                    "quantidade": linha["quantidade"],
                    "preco_unitario": linha["preco_unitario"],
                })
        return list(pedidos.values())

    def buscar_por_id(self, pedido_id):
        linha = self._conn.execute(
            "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE id = ?",
            (pedido_id,),
        ).fetchone()
        return dict(linha) if linha else None

    def listar_itens(self, pedido_id):
        linhas = self._conn.execute(
            "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id = ? ORDER BY id",
            (pedido_id,),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def inserir(self, usuario_id, status, total):
        cursor = self._conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, status, total),
        )
        return cursor.lastrowid

    def inserir_item(self, pedido_id, produto_id, quantidade, preco_unitario):
        self._conn.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    def trocar_status(self, pedido_id, status_atual, novo_status):
        """Troca o status só se ele ainda for `status_atual`. Devolve False se não trocou."""
        cursor = self._conn.execute(
            "UPDATE pedidos SET status = ? WHERE id = ? AND status IS ?",
            (novo_status, pedido_id, status_atual),
        )
        return cursor.rowcount == 1

    def totais_por_status(self):
        """Quantidade de pedidos e soma dos totais, agrupadas por status."""
        linhas = self._conn.execute(
            "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS total "
            "FROM pedidos GROUP BY status"
        ).fetchall()
        return {linha["status"]: {"quantidade": linha["quantidade"], "total": linha["total"]} for linha in linhas}
