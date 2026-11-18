"""Fluxo das requisições de pedidos."""
from flask import jsonify, request

from src.middlewares.auth import eh_admin, exigir_dono, exigir_usuario
from src.utils.errors import AppError
from src.utils.validators import corpo_json, exigir_inteiro, paginacao

_ITEM_INVALIDO = "Cada item deve informar produto_id e quantidade inteiros maiores que zero"


def _ler_item(item):
    if not isinstance(item, dict):
        raise AppError(_ITEM_INVALIDO, status=400)
    return {
        "produto_id": exigir_inteiro(item.get("produto_id"), _ITEM_INVALIDO, minimo=1),
        "quantidade": exigir_inteiro(item.get("quantidade"), _ITEM_INVALIDO, minimo=1),
    }


class PedidoController:
    def __init__(self, pedido_service):
        self.pedidos = pedido_service

    def criar(self):
        exigir_usuario()  # 401 antes de olhar o corpo
        dados = corpo_json(request)
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise AppError("Usuario ID é obrigatório", status=400)
        exigir_inteiro(usuario_id, "Usuario ID deve ser um número inteiro", minimo=1)
        exigir_dono(usuario_id)  # o pedido é criado em nome da conta informada
        if not isinstance(itens, list) or len(itens) == 0:
            raise AppError("Pedido deve ter pelo menos 1 item", status=400)

        resultado = self.pedidos.criar(usuario_id, [_ler_item(item) for item in itens])
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_do_usuario(self, usuario_id):
        limite, offset = paginacao(request.args)
        pedidos = self.pedidos.listar_do_usuario(usuario_id, limite, offset)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def listar_todos(self):
        limite, offset = paginacao(request.args)
        return jsonify({"dados": self.pedidos.listar_todos(limite, offset), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        conta_id = exigir_usuario()
        if not eh_admin():
            # Pedido de outra conta e pedido inexistente respondem igual, para não
            # revelar a quem não é dono quais pedidos existem.
            dono = self.pedidos.dono_do_pedido(pedido_id)
            if dono is None or dono != conta_id:
                raise AppError("Acesso negado a este pedido", status=403)

        dados = corpo_json(request, obrigatorio=False)
        self.pedidos.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
