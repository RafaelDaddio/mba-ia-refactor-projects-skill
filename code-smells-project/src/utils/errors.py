"""Erro de aplicação lançado por services, controllers e middlewares."""


class AppError(Exception):
    """Erro esperado: mensagem para o cliente e status HTTP da resposta."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status
