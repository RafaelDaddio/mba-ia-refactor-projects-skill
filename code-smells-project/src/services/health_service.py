class HealthService:
    def __init__(self, produtos, usuarios, pedidos):
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos

    def contagens(self):
        return {
            "produtos": self.produtos.contar(),
            "usuarios": self.usuarios.contar(),
            "pedidos": self.pedidos.contar(),
        }
