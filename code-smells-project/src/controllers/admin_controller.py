"""Fluxo das requisições administrativas."""
from flask import jsonify, request

from src.utils.validators import objeto_json


class AdminController:
    def __init__(self, service):
        self.service = service

    def reset_database(self):
        self.service.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        dados = objeto_json(request.get_json(silent=True), permitir_vazio=True)
        linhas = self.service.executar_query(dados.get("sql", ""))
        if linhas is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": linhas, "sucesso": True}), 200
