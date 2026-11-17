"""Regras de negócio de pedidos: estoque, total, status e notificações."""
from src.utils.errors import AppError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]


class PedidoService:
    def __init__(self, pedidos, produtos, usuarios, notificacoes, transacao):
        self.pedidos = pedidos
        self.produtos = produtos
        self.usuarios = usuarios
        self.notificacoes = notificacoes
        self.transacao = transacao  # unidade de trabalho: tudo ou nada

    def listar_todos(self, limite, offset):
        return self.pedidos.listar(limite, offset)

    def listar_do_usuario(self, usuario_id, limite, offset):
        return self.pedidos.listar(limite, offset, usuario_id=usuario_id)

    def dono_do_pedido(self, pedido_id):
        """Id da conta dona do pedido, ou None se o pedido não existe."""
        pedido = self.pedidos.buscar_por_id(pedido_id)
        return pedido["usuario_id"] if pedido else None

    def criar(self, usuario_id, itens):
        with self.transacao():
            if self.usuarios.buscar_por_id(usuario_id) is None:
                raise AppError("Usuário " + str(usuario_id) + " não encontrado")

            # O estoque é conferido pela soma das quantidades de cada produto no pedido.
            quantidades = {}
            for item in itens:
                quantidades[item["produto_id"]] = quantidades.get(item["produto_id"], 0) + item["quantidade"]

            produtos = {}
            for produto_id, quantidade in quantidades.items():
                produto = self.produtos.buscar_por_id(produto_id)
                if produto is None:
                    raise AppError("Produto " + str(produto_id) + " não encontrado")
                if produto["estoque"] < quantidade:
                    raise AppError("Estoque insuficiente para " + produto["nome"])
                produtos[produto_id] = produto

            total = 0
            for item in itens:
                total = total + produtos[item["produto_id"]]["preco"] * item["quantidade"]

            pedido_id = self.pedidos.inserir(usuario_id, STATUS_PENDENTE, total)
            for item in itens:
                produto = produtos[item["produto_id"]]
                self.pedidos.inserir_item(pedido_id, produto["id"], item["quantidade"], produto["preco"])
            for produto_id, quantidade in quantidades.items():
                self._baixar_estoque(produto_id, quantidade)

        self.notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_VALIDOS:
            raise AppError("Status inválido")

        with self.transacao():
            pedido = self.pedidos.buscar_por_id(pedido_id)
            if pedido is None:
                raise AppError("Pedido não encontrado", status=404)

            # O estoque acompanha o cancelamento: devolvido ao cancelar (uma única vez)
            # e baixado de novo se o pedido cancelado for reativado.
            estava_cancelado = pedido["status"] == STATUS_CANCELADO
            cancelando = novo_status == STATUS_CANCELADO and not estava_cancelado
            reativando = estava_cancelado and novo_status != STATUS_CANCELADO
            if cancelando:
                for produto_id, quantidade in self.pedidos.quantidades_por_produto(pedido_id):
                    self.produtos.devolver_estoque(produto_id, quantidade)
            elif reativando:
                for produto_id, quantidade in self.pedidos.quantidades_por_produto(pedido_id):
                    self._baixar_estoque(produto_id, quantidade)

            self.pedidos.atualizar_status(pedido_id, novo_status)

        if novo_status == STATUS_APROVADO:
            self.notificacoes.pedido_aprovado(pedido_id)
        if cancelando:
            self.notificacoes.pedido_cancelado(pedido_id)

    def _baixar_estoque(self, produto_id, quantidade):
        if self.produtos.baixar_estoque(produto_id, quantidade):
            return
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is not None:  # produto excluído depois do pedido: não há estoque a baixar
            raise AppError("Estoque insuficiente para " + produto["nome"])
