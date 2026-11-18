"""Regras de negócio de produtos."""
import logging

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200


class ProdutoService:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self, limite, offset):
        produtos = self.produtos.listar(limite, offset)
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is None:
            raise AppError("Produto não encontrado", status=404)
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max, limite, offset):
        return self.produtos.buscar(termo, categoria, preco_min, preco_max, limite, offset)

    def criar(self, nome, descricao, preco, estoque, categoria=None):
        categoria = self._validar(nome, preco, estoque, categoria)
        with self.produtos.transacao():
            produto_id = self.produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria=None):
        categoria = self._validar(nome, preco, estoque, categoria)
        with self.produtos.transacao():
            atualizado = self.produtos.atualizar(produto_id, nome, descricao, preco, estoque, categoria)
        if not atualizado:
            raise AppError("Produto não encontrado", status=404)

    def deletar(self, produto_id):
        with self.produtos.transacao():
            deletado = self.produtos.deletar(produto_id)
        if not deletado:
            raise AppError("Produto não encontrado", status=404)
        logger.info("Produto %s deletado", produto_id)

    @staticmethod
    def _validar(nome, preco, estoque, categoria):
        """Regras do produto, as mesmas para criar e atualizar. Devolve a categoria efetiva."""
        if categoria is None:
            categoria = CATEGORIA_PADRAO
        if preco < 0:
            raise AppError("Preço não pode ser negativo", status=400)
        if estoque < 0:
            raise AppError("Estoque não pode ser negativo", status=400)
        if len(nome) < NOME_TAMANHO_MINIMO:
            raise AppError("Nome muito curto", status=400)
        if len(nome) > NOME_TAMANHO_MAXIMO:
            raise AppError("Nome muito longo", status=400)
        if categoria not in CATEGORIAS_VALIDAS:
            raise AppError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS), status=400)
        return categoria
