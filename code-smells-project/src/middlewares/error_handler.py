import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def resposta_de_erro(mensagem, status):
    """Formato único de erro da API."""
    return jsonify({"erro": mensagem, "sucesso": False}), status


def registrar_tratamento_de_erros(app):
    @app.errorhandler(AppError)
    def _erro_da_aplicacao(erro):
        return resposta_de_erro(erro.mensagem, erro.status)

    @app.errorhandler(HTTPException)
    def _erro_http(erro):
        return resposta_de_erro(erro.description, erro.code)

    @app.errorhandler(Exception)
    def _erro_inesperado(_erro):
        logger.exception("Erro inesperado ao processar a requisição")
        return resposta_de_erro("Erro interno do servidor", 500)
