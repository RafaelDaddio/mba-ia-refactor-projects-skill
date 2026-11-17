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
    415: "Content-Type não suportado",
}


def _erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _erro(err.message, err.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return _erro(_MENSAGENS_HTTP.get(err.code, err.name), err.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return _erro("Erro interno do servidor", 500)
