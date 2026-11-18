"""Fluxo das requisições gerais: raiz e health check."""
from flask import jsonify


class SistemaController:
    def __init__(self, sistema_service):
        self.sistema = sistema_service

    def index(self):
        return jsonify(self.sistema.apresentacao())

    def health_check(self):
        return jsonify(self.sistema.saude()), 200
