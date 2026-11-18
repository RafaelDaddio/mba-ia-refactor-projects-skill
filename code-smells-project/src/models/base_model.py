"""Base dos models: recebem da composition root a função que entrega a conexão."""


class BaseModel:
    def __init__(self, obter_conexao):
        self._obter_conexao = obter_conexao

    @property
    def _conn(self):
        return self._obter_conexao()

    def transacao(self):
        """Gerenciador de contexto da transação: commit ao sair, rollback em exceção.

        Os models não fazem commit; os services delimitam cada escrita com
        `with model.transacao():`. Todos os models de uma requisição compartilham
        a mesma conexão, então a transação cobre as escritas de todos eles.
        """
        return self._obter_conexao()
