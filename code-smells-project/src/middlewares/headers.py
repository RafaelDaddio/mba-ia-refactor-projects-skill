"""Header `Server` sem nome nem versão da stack."""
from werkzeug.serving import WSGIRequestHandler

SERVER_HEADER = "loja-api"


class RequestHandlerSemVersao(WSGIRequestHandler):
    """Handler do servidor embutido (`app.run`).

    O padrão anuncia "Werkzeug/x.y Python/x.y" em toda resposta; esse header é
    escrito pelo próprio servidor, antes dos headers da aplicação.
    """

    def version_string(self):
        return SERVER_HEADER
