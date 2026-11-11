from src.models.pedido_model import EstoqueInsuficiente
from src.utils.errors import AppError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]


class PedidoService:
    def __init__(self, pedidos, produtos, usuarios, notificacoes):
        self.pedidos = pedidos
        self.produtos = produtos
        self.usuarios = usuarios
        self.notificacoes = notificacoes

    def listar(self, limite, deslocamento, usuario_id=None):
        return self.pedidos.listar(limite, deslocamento, usuario_id=usuario_id)

    def criar(self, usuario_id, itens):
        """`itens`: lista de {"produto_id": int, "quantidade": int > 0}, já validada pelo controller."""
        if self.usuarios.buscar_por_id(usuario_id) is None:
            raise AppError(f"Usuário {usuario_id} não encontrado")

        produtos = self.produtos.buscar_por_ids({item["produto_id"] for item in itens})
        total = 0
        reservado = {}
        linhas = []
        for item in itens:
            produto_id, quantidade = item["produto_id"], item["quantidade"]
            produto = produtos.get(produto_id)
            if produto is None:
                raise AppError(f"Produto {produto_id} não encontrado")
            # Soma as linhas do mesmo produto antes de comparar com o estoque.
            reservado[produto_id] = reservado.get(produto_id, 0) + quantidade
            if produto["estoque"] < reservado[produto_id]:
                raise AppError(f"Estoque insuficiente para {produto['nome']}")
            total = total + (produto["preco"] * quantidade)
            linhas.append((produto_id, quantidade, produto["preco"]))

        try:
            pedido_id = self.pedidos.criar(usuario_id, STATUS_PENDENTE, total, linhas)
        except EstoqueInsuficiente as erro:
            raise AppError(f"Estoque insuficiente para {produtos[erro.produto_id]['nome']}") from None

        self.notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_VALIDOS:
            raise AppError("Status inválido")
        if self.pedidos.buscar_por_id(pedido_id) is None:
            raise AppError("Pedido não encontrado", status=404)

        if novo_status == STATUS_CANCELADO:
            if self.pedidos.cancelar_devolvendo_estoque(pedido_id, STATUS_CANCELADO):
                self.notificacoes.pedido_cancelado(pedido_id)
            return

        self.pedidos.atualizar_status(pedido_id, novo_status)
        if novo_status == STATUS_APROVADO:
            self.notificacoes.pedido_aprovado(pedido_id)
