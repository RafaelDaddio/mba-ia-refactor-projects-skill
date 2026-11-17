"""Regras de negócio de produtos."""
import logging

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MIN = 2
NOME_TAMANHO_MAX = 200


class ProdutoService:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self, limite, offset):
        return self.produtos.listar(limite, offset)

    def obter(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is None:
            raise AppError("Produto não encontrado", status=404)
        return produto

    def buscar(self, limite, offset, termo="", categoria=None, preco_min=None, preco_max=None):
        # Como no comportamento original, preço 0 equivale a filtro não informado.
        return self.produtos.buscar(
            limite, offset, termo=termo, categoria=categoria,
            preco_min=preco_min or None, preco_max=preco_max or None,
        )

    def criar(self, dados):
        self._validar(dados)
        produto_id = self.produtos.inserir(
            dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]
        )
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        self.obter(produto_id)
        self._validar(dados)
        self.produtos.atualizar(
            produto_id, dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]
        )

    def deletar(self, produto_id):
        self.obter(produto_id)
        self.produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)

    @staticmethod
    def _validar(dados):
        """Regras de domínio, as mesmas para criar e atualizar."""
        if dados["preco"] < 0:
            raise AppError("Preço não pode ser negativo")
        if dados["estoque"] < 0:
            raise AppError("Estoque não pode ser negativo")
        if len(dados["nome"]) < NOME_TAMANHO_MIN:
            raise AppError("Nome muito curto")
        if len(dados["nome"]) > NOME_TAMANHO_MAX:
            raise AppError("Nome muito longo")
        if dados["categoria"] not in CATEGORIAS_VALIDAS:
            raise AppError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
