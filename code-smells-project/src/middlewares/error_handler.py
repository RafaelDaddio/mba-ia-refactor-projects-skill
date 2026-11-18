"""Tratamento de erros centralizado: todo erro sai como {"erro": ..., "sucesso": false}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

_MENSAGENS_HTTP = {
    400: "Requisição inválida",
    404: "Recurso não encontrado",
    405: "Método não permitido",
    415: "Content-Type deve ser application/json",
}


def _erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(erro):
        return _erro(erro.message, erro.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(erro):
        return _erro(_MENSAGENS_HTTP.get(erro.code, erro.description), erro.code)

    @app.errorhandler(Exception)
    def handle_unexpected(erro):
        logger.exception("Erro inesperado")
        return _erro("Erro interno do servidor", 500)
