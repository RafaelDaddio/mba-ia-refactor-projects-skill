from flask import Blueprint

from src.middlewares.auth import exigir_admin, exigir_recurso_habilitado


def criar_blueprint(controller):
    bp = Blueprint("admin", __name__)
    bp.add_url_rule(
        "/admin/reset-db", "reset_database", exigir_admin(controller.resetar_banco), methods=["POST"]
    )
    # Executar SQL recebido fica desligado por padrão (ALLOW_ADMIN_SQL), mesmo com o token.
    bp.add_url_rule(
        "/admin/query",
        "executar_query",
        exigir_admin(exigir_recurso_habilitado("ALLOW_ADMIN_SQL")(controller.executar_query)),
        methods=["POST"],
    )
    return bp
