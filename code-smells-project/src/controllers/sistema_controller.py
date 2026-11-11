from flask import jsonify


class SistemaController:
    def __init__(self, health_service, versao_api):
        self.health_service = health_service
        self.versao_api = versao_api

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.versao_api,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": self.health_service.contagens(),
            "versao": self.versao_api,
        }), 200
