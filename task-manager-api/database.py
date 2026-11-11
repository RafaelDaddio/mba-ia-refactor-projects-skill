"""Extensão do banco, criação do schema e commit transacional."""
import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from utils.errors import PersistenceError

logger = logging.getLogger(__name__)

db = SQLAlchemy()


def init_db(app):
    """Liga o banco à aplicação e cria as tabelas que ainda não existem."""
    db.init_app(app)
    import models  # noqa: F401 — registra os models antes do create_all

    with app.app_context():
        db.create_all()


def commit():
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception("Falha ao gravar no banco")
        raise PersistenceError(str(exc)) from exc
