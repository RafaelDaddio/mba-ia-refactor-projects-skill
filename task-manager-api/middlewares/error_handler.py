"""Tratamento de erros centralizado: toda falha sai como {"error": mensagem}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

ERROR_KEY = 'error'
HTTP_MESSAGES = {
    400: 'Requisição inválida',
    404: 'Recurso não encontrado',
    405: 'Método não permitido',
    415: 'Content-Type deve ser application/json',
}


def _error(message, status):
    return jsonify({ERROR_KEY: message}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _error(err.message, err.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return _error(HTTP_MESSAGES.get(err.code, err.description), err.code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception('Erro inesperado')
        return _error('Erro interno do servidor', 500)
