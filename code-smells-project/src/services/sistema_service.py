"""Informações gerais da API: apresentação e health check."""

VERSAO = "1.0.0"


class SistemaService:
    def __init__(self, sistema):
        self.sistema = sistema

    def apresentacao(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": VERSAO,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }

    def saude(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": self.sistema.contagens(),
            "versao": VERSAO,
        }
