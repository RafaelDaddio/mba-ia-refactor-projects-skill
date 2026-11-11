from flask import jsonify, request

from src.services.produto_service import CATEGORIA_PADRAO
from src.utils.errors import AppError
from src.utils.validators import (
    como_inteiro,
    eh_numero,
    exigir_objeto,
    numero_opcional,
    paginacao,
)

CAMPOS_OBRIGATORIOS = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _campos_produto(dados):
    """Validação de entrada compartilhada entre cadastro e atualização."""
    dados = exigir_objeto(dados)
    for campo, mensagem in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            raise AppError(mensagem)

    nome = dados["nome"]
    if not isinstance(nome, str):
        raise AppError("Nome deve ser um texto")
    preco = dados["preco"]
    if not eh_numero(preco):
        raise AppError("Preço deve ser numérico")
    estoque = como_inteiro(dados["estoque"])
    if estoque is None:
        raise AppError("Estoque deve ser um número inteiro")
    descricao = dados.get("descricao", "")
    if descricao is None:
        descricao = ""
    if not isinstance(descricao, str):
        raise AppError("Descrição deve ser um texto")

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": dados.get("categoria", CATEGORIA_PADRAO),
    }


class ProdutoController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        limite, deslocamento = paginacao(request.args.get("limit"), request.args.get("offset"))
        produtos = self.service.listar(limite, deslocamento)
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def obter(self, produto_id):
        return jsonify({"dados": self.service.obter(produto_id), "sucesso": True}), 200

    def buscar(self):
        limite, deslocamento = paginacao(request.args.get("limit"), request.args.get("offset"))
        resultados = self.service.buscar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=numero_opcional(request.args.get("preco_min"), "preco_min"),
            preco_max=numero_opcional(request.args.get("preco_max"), "preco_max"),
            limite=limite,
            deslocamento=deslocamento,
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        campos = _campos_produto(request.get_json(silent=True))
        produto_id = self.service.criar(**campos)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        self.service.obter(produto_id)  # 404 antes de validar o corpo, como na versão original
        campos = _campos_produto(request.get_json(silent=True))
        self.service.atualizar(produto_id, **campos)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def excluir(self, produto_id):
        self.service.excluir(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
