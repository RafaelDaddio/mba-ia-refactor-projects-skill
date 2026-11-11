from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import como_id, como_inteiro, exigir_objeto, paginacao


def _itens_do_pedido(itens):
    if not isinstance(itens, list):
        raise AppError("Itens do pedido devem ser uma lista")
    validados = []
    for item in itens:
        if not isinstance(item, dict):
            raise AppError("Item do pedido inválido")
        produto_id = como_id(item.get("produto_id"))
        if produto_id is None:
            raise AppError("Produto ID inválido")
        quantidade = como_inteiro(item.get("quantidade"))
        if quantidade is None or quantidade < 1:
            raise AppError("Quantidade deve ser um número inteiro maior que zero")
        validados.append({"produto_id": produto_id, "quantidade": quantidade})
    return validados


class PedidoController:
    def __init__(self, service):
        self.service = service

    def criar(self):
        dados = exigir_objeto(request.get_json(silent=True))
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise AppError("Usuario ID é obrigatório")
        if not itens:
            raise AppError("Pedido deve ter pelo menos 1 item")
        usuario_id = como_id(usuario_id)
        if usuario_id is None:
            raise AppError("Usuario ID inválido")

        resultado = self.service.criar(usuario_id, _itens_do_pedido(itens))
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar(self):
        limite, deslocamento = paginacao(request.args.get("limit"), request.args.get("offset"))
        return jsonify({"dados": self.service.listar(limite, deslocamento), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        limite, deslocamento = paginacao(request.args.get("limit"), request.args.get("offset"))
        pedidos = self.service.listar(limite, deslocamento, usuario_id=usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        dados = exigir_objeto(request.get_json(silent=True), permitir_vazio=True)
        self.service.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
