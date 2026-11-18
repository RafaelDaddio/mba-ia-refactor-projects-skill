"""Rotas públicas gerais: raiz e health check."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health_check, methods=["GET"])
    return bp
