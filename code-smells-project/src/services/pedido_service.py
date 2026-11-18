"""Regras de negócio de pedidos: estoque, total e mudança de status."""
from src.utils.errors import AppError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]


class PedidoService:
    def __init__(self, pedidos, produtos, usuarios, notificador):
        self.pedidos = pedidos
        self.produtos = produtos
        self.usuarios = usuarios
        self.notificador = notificador

    def listar_todos(self, limite, offset):
        return self.pedidos.listar(limite, offset)

    def listar_do_usuario(self, usuario_id, limite, offset):
        return self.pedidos.listar(limite, offset, usuario_id=usuario_id)

    def dono_do_pedido(self, pedido_id):
        """Id da conta dona do pedido, ou None se o pedido não existe."""
        pedido = self.pedidos.buscar_por_id(pedido_id)
        return pedido["usuario_id"] if pedido else None

    def criar(self, usuario_id, itens):
        """Cria o pedido. `itens`: lista de {"produto_id": int, "quantidade": int > 0}."""
        if self.usuarios.buscar_por_id(usuario_id) is None:
            raise AppError("Usuário " + str(usuario_id) + " não encontrado", status=400)

        linhas, total = [], 0
        for item in itens:
            produto = self.produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise AppError("Produto " + str(item["produto_id"]) + " não encontrado", status=400)
            if produto["estoque"] < item["quantidade"]:
                raise AppError("Estoque insuficiente para " + produto["nome"], status=400)
            linhas.append((produto, item["quantidade"]))
            total = total + (produto["preco"] * item["quantidade"])

        with self.pedidos.transacao():  # tudo ou nada
            pedido_id = self.pedidos.inserir(usuario_id, STATUS_PENDENTE, total)
            for produto, quantidade in linhas:
                self.pedidos.inserir_item(pedido_id, produto["id"], quantidade, produto["preco"])
                # Baixa condicional: cobre produto repetido no pedido e pedidos concorrentes.
                if not self.produtos.baixar_estoque(produto["id"], quantidade):
                    raise AppError("Estoque insuficiente para " + produto["nome"], status=400)

        self.notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_VALIDOS:
            raise AppError("Status inválido", status=400)
        pedido = self.pedidos.buscar_por_id(pedido_id)
        if pedido is None:
            raise AppError("Pedido não encontrado", status=404)

        status_atual = pedido["status"]
        cancelando = novo_status == STATUS_CANCELADO and status_atual != STATUS_CANCELADO
        reabrindo = status_atual == STATUS_CANCELADO and novo_status != STATUS_CANCELADO

        with self.pedidos.transacao():
            if not self.pedidos.trocar_status(pedido_id, status_atual, novo_status):
                raise AppError("Pedido alterado por outra requisição; tente novamente", status=409)
            # O estoque acompanha o cancelamento: devolvido ao cancelar (uma única vez)
            # e reservado de novo se o pedido deixar de estar cancelado.
            if cancelando:
                for item in self.pedidos.listar_itens(pedido_id):
                    self.produtos.devolver_estoque(item["produto_id"], item["quantidade"])
            elif reabrindo:
                for item in self.pedidos.listar_itens(pedido_id):
                    self._reservar_estoque(item["produto_id"], item["quantidade"])

        if novo_status == STATUS_APROVADO:
            self.notificador.pedido_aprovado(pedido_id)
        if cancelando:
            self.notificador.pedido_cancelado(pedido_id)

    def _reservar_estoque(self, produto_id, quantidade):
        if self.produtos.baixar_estoque(produto_id, quantidade):
            return
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is not None:  # produto excluído não tem estoque a reservar
            raise AppError("Estoque insuficiente para " + produto["nome"], status=400)
