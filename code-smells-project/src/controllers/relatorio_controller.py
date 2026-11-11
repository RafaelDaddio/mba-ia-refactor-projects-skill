from flask import jsonify


class RelatorioController:
    def __init__(self, service):
        self.service = service

    def vendas(self):
        return jsonify({"dados": self.service.vendas(), "sucesso": True}), 200
