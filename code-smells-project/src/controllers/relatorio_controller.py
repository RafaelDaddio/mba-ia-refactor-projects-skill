"""Fluxo das requisições de relatórios."""
from flask import jsonify


class RelatorioController:
    def __init__(self, relatorio_service):
        self.relatorios = relatorio_service

    def vendas(self):
        return jsonify({"dados": self.relatorios.vendas(), "sucesso": True}), 200
