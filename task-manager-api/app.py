"""Entry point: `python app.py`. Expõe `app` e `db` para scripts auxiliares (seed.py)."""
from app_factory import create_app
from config.settings import Settings
from database import db  # noqa: F401 — reexportado para `from app import app, db`

settings = Settings()
app = create_app(settings)

if __name__ == '__main__':
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
