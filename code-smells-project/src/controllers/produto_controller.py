"""Fluxo das requisições de produtos: lê e valida a entrada, chama o service, responde."""
from flask import jsonify, request

from src.services.produto_service import CATEGORIA_PADRAO
from src.utils.errors import AppError
from src.utils.validators import inteiro, numero, objeto_json, paginacao, query_float, texto


def _ler_produto(dados):
    """Presença e tipo dos campos, iguais para criar e atualizar."""
    dados = objeto_json(dados)
    if "nome" not in dados:
        raise AppError("Nome é obrigatório")
    if "preco" not in dados:
        raise AppError("Preço é obrigatório")
    if "estoque" not in dados:
        raise AppError("Estoque é obrigatório")
    return {
        "nome": texto(dados["nome"], "Nome deve ser um texto"),
        "descricao": texto(dados.get("descricao", ""), "Descrição deve ser um texto"),
        "preco": numero(dados["preco"], "Preço deve ser numérico"),
        "estoque": inteiro(dados["estoque"], "Estoque deve ser um número inteiro"),
        "categoria": dados.get("categoria", CATEGORIA_PADRAO),
    }


class ProdutoController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        limite, offset = paginacao(request.args)
        produtos = self.service.listar(limite, offset)
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar_por_id(self, produto_id):
        return jsonify({"dados": self.service.obter(produto_id), "sucesso": True}), 200

    def buscar(self):
        limite, offset = paginacao(request.args)
        resultados = self.service.buscar(
            limite, offset,
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=query_float(request.args, "preco_min"),
            preco_max=query_float(request.args, "preco_max"),
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        produto_id = self.service.criar(_ler_produto(request.get_json(silent=True)))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        self.service.obter(produto_id)  # 404 tem precedência sobre os erros do corpo
        self.service.atualizar(produto_id, _ler_produto(request.get_json(silent=True)))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self.service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
