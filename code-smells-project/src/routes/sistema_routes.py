"""Rotas públicas de sistema."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/", view_func=controller.index, methods=["GET"])
    bp.add_url_rule("/health", view_func=controller.health_check, methods=["GET"])
    return bp
