"""Fluxo das requisições de produtos."""
from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import (
    corpo_json,
    exigir_inteiro,
    exigir_numero,
    exigir_texto,
    paginacao,
    query_float,
)

_OBRIGATORIOS = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _ler_produto():
    """Campos do produto no corpo da requisição, já com os tipos conferidos."""
    dados = corpo_json(request)
    for campo, mensagem in _OBRIGATORIOS:
        if campo not in dados:
            raise AppError(mensagem, status=400)
    categoria = dados.get("categoria")
    return {
        "nome": exigir_texto(dados["nome"], "Nome deve ser um texto"),
        "descricao": exigir_texto(dados.get("descricao", ""), "Descrição deve ser um texto"),
        "preco": exigir_numero(dados["preco"], "Preço deve ser numérico"),
        "estoque": exigir_inteiro(dados["estoque"], "Estoque deve ser um número inteiro"),
        "categoria": None if categoria is None else exigir_texto(categoria, "Categoria deve ser um texto"),
    }


class ProdutoController:
    def __init__(self, produto_service):
        self.produtos = produto_service

    def listar(self):
        limite, offset = paginacao(request.args)
        return jsonify({"dados": self.produtos.listar(limite, offset), "sucesso": True}), 200

    def buscar_por_id(self, produto_id):
        return jsonify({"dados": self.produtos.obter(produto_id), "sucesso": True}), 200

    def buscar(self):
        limite, offset = paginacao(request.args)
        resultados = self.produtos.buscar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=query_float(request.args, "preco_min"),
            preco_max=query_float(request.args, "preco_max"),
            limite=limite,
            offset=offset,
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        produto_id = self.produtos.criar(**_ler_produto())
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        self.produtos.obter(produto_id)  # 404 antes de validar o corpo, como no contrato original
        self.produtos.atualizar(produto_id, **_ler_produto())
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self.produtos.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
