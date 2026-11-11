"""Erros de aplicação."""
from contextlib import contextmanager


class AppError(Exception):
    """Erro com mensagem para o cliente e status HTTP; convertido em JSON pelo handler central."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


class PersistenceError(Exception):
    """Falha ao gravar no banco; a transação já foi desfeita."""


@contextmanager
def persistence_failure(message):
    """Converte uma falha de gravação no erro 500 que o endpoint já devolvia."""
    try:
        yield
    except PersistenceError:
        raise AppError(message, status=500) from None
