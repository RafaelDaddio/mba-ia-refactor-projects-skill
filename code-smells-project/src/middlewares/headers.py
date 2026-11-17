"""Header Server: não revelar o servidor nem as versões da stack."""
from werkzeug.serving import WSGIRequestHandler

SERVER_HEADER = "API"


class RequestHandlerSemVersao(WSGIRequestHandler):
    """Handler do servidor embutido que troca "Werkzeug/x Python/y" por um nome genérico."""

    def version_string(self):
        return SERVER_HEADER
