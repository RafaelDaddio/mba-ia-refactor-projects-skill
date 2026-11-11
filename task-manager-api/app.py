"""Composition root e entry point (`python app.py`)."""
from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db, init_db
from middlewares.error_handler import register_error_handlers
from routes import category_routes, health_routes, report_routes, task_routes, user_routes
from utils.logger import configure_logging

BLUEPRINT_MODULES = (health_routes, task_routes, user_routes, category_routes, report_routes)

__all__ = ["app", "create_app", "db"]


def create_app(settings=None):
    settings = settings or Settings()
    configure_logging(settings.debug)

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
        ADMIN_TOKEN=settings.admin_token,
    )
    CORS(app, origins=settings.cors_origins)
    init_db(app)
    register_error_handlers(app)

    for module in BLUEPRINT_MODULES:
        app.register_blueprint(module.bp)

    return app


settings = Settings()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
