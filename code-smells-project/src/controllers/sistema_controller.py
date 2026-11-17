"""Fluxo das requisições de sistema: índice e health check."""
from flask import jsonify


class SistemaController:
    def __init__(self, service):
        self.service = service

    def index(self):
        return jsonify(self.service.indice())

    def health_check(self):
        return jsonify(self.service.saude()), 200
