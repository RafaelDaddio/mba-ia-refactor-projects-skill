class AppError(Exception):
    """Erro esperado da aplicação: mensagem para o cliente e status HTTP."""

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
