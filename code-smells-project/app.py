"""Ponto de entrada: `python app.py`. A aplicação é montada em src/app.py."""
import logging

from src.app import create_app
from src.config.settings import Settings
from src.middlewares.headers import RequestHandlerSemVersao

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        request_handler=RequestHandlerSemVersao,
    )
