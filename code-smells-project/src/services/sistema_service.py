"""Informações do sistema: índice da API e health check."""

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SistemaService:
    def __init__(self, produtos, usuarios, pedidos, versao):
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos
        self.versao = versao

    def indice(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.versao,
            "endpoints": ENDPOINTS,
        }

    def saude(self):
        """Só dados não sensíveis: nada de segredos, caminhos ou flags internas."""
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            },
            "versao": self.versao,
        }
