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

    def listar(self, limite, deslocamento):
        produtos = self.produtos.listar(limite, deslocamento)
        logger.debug("Listando %s produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is None:
            raise AppError("Produto não encontrado", status=404)
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max, limite, deslocamento):
        return self.produtos.buscar(termo, categoria, preco_min, preco_max, limite, deslocamento)

    def criar(self, nome, descricao, preco, estoque, categoria):
        self._validar_regras(nome, preco, estoque, categoria)
        produto_id = self.produtos.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self.obter(produto_id)
        self._validar_regras(nome, preco, estoque, categoria)
        self.produtos.atualizar(produto_id, nome, descricao, preco, estoque, categoria)

    def excluir(self, produto_id):
        self.obter(produto_id)
        self.produtos.excluir(produto_id)
        logger.info("Produto %s deletado", produto_id)

    @staticmethod
    def _validar_regras(nome, preco, estoque, categoria):
        """Mesmas regras no cadastro e na atualização."""
        if preco < 0:
            raise AppError("Preço não pode ser negativo")
        if estoque < 0:
            raise AppError("Estoque não pode ser negativo")
        if len(nome) < NOME_TAMANHO_MINIMO:
            raise AppError("Nome muito curto")
        if len(nome) > NOME_TAMANHO_MAXIMO:
            raise AppError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise AppError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
