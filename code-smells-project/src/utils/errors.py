"""Erro de aplicação: mensagem para o cliente e status HTTP."""


class AppError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status
