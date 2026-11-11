"""Tratamento de erros centralizado: toda falha sai como JSON {"error": ...}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)
ERROR_KEY = 'error'


def _error(message, status):
    return jsonify({ERROR_KEY: message}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _error(err.message, err.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        response, status = _error(err.description, err.code)
        for header, value in err.get_headers():
            if header.lower() != 'content-type':  # preserva, por exemplo, o Allow do 405
                response.headers[header] = value
        return response, status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception('Erro inesperado')
        return _error('Erro interno do servidor', 500)
