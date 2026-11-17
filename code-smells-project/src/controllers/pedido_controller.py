"""Fluxo das requisições de pedidos."""
from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import inteiro, objeto_json, paginacao


def _ler_item(item):
    if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
        raise AppError("Cada item deve informar produto_id e quantidade")
    return {
        "produto_id": inteiro(item["produto_id"], "produto_id deve ser um número inteiro"),
        "quantidade": inteiro(item["quantidade"], "Quantidade deve ser um inteiro maior que zero", minimo=1),
    }


class PedidoController:
    def __init__(self, service, auth):
        self.service = service
        self.auth = auth

    def criar(self):
        self.auth.require_user()  # credencial antes de olhar o corpo
        dados = objeto_json(request.get_json(silent=True))
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise AppError("Usuario ID é obrigatório")
        usuario_id = inteiro(usuario_id, "Usuario ID deve ser um número inteiro")
        self.auth.require_account_owner(usuario_id)  # agir em nome da conta informada
        if not isinstance(itens, list) or len(itens) == 0:
            raise AppError("Pedido deve ter pelo menos 1 item")

        resultado = self.service.criar(usuario_id, [_ler_item(item) for item in itens])
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_do_usuario(self, usuario_id):
        self.auth.require_account_owner(usuario_id)
        limite, offset = paginacao(request.args)
        pedidos = self.service.listar_do_usuario(usuario_id, limite, offset)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def listar_todos(self):
        limite, offset = paginacao(request.args)
        return jsonify({"dados": self.service.listar_todos(limite, offset), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        self.auth.require_user()
        if not self.auth.is_admin():
            # Pedido de outra conta e pedido inexistente (dono None) respondem o mesmo 403,
            # para não revelar quais pedidos existem.
            self.auth.require_account_owner(self.service.dono_do_pedido(pedido_id))

        dados = objeto_json(request.get_json(silent=True), permitir_vazio=True)
        self.service.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
