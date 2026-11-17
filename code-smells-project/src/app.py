"""Composition root: cria a aplicação e injeta as dependências de cada camada."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import VERSAO_API, Settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database import Database, init_db
from src.middlewares.auth import Auth
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.routes import (
    admin_routes,
    pedido_routes,
    produto_routes,
    relatorio_routes,
    sistema_routes,
    usuario_routes,
)
from src.services.admin_service import AdminService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.sistema_service import SistemaService
from src.services.usuario_service import UsuarioService
from src.utils.logger import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or Settings()
    configure_logging(settings.debug)
    if settings.secret_key_temporaria:
        logger.warning(
            "SECRET_KEY não definida: usando chave aleatória temporária. "
            "Os tokens de login deixam de valer a cada reinício."
        )

    app = Flask(__name__)
    if settings.cors_origins:  # sem origens configuradas, nenhuma origem externa é liberada
        CORS(app, origins=settings.cors_origins)
    register_error_handlers(app)

    db = Database(settings.database_path)
    init_db(app, db, seed=settings.seed_on_start, senha_admin=settings.seed_admin_password)
    auth = Auth(settings.secret_key, settings.admin_token)

    produtos = ProdutoModel(db)
    usuarios = UsuarioModel(db)
    pedidos = PedidoModel(db)

    produto_service = ProdutoService(produtos)
    usuario_service = UsuarioService(usuarios)
    pedido_service = PedidoService(pedidos, produtos, usuarios, NotificacaoService(), db.transaction)
    relatorio_service = RelatorioService(pedidos)
    sistema_service = SistemaService(produtos, usuarios, pedidos, VERSAO_API)
    admin_service = AdminService(AdminModel(db), sql_habilitado=settings.allow_admin_sql)

    blueprints = (
        sistema_routes.criar_blueprint(SistemaController(sistema_service)),
        produto_routes.criar_blueprint(ProdutoController(produto_service), auth),
        usuario_routes.criar_blueprint(UsuarioController(usuario_service, auth), auth),
        pedido_routes.criar_blueprint(PedidoController(pedido_service, auth), auth),
        relatorio_routes.criar_blueprint(RelatorioController(relatorio_service), auth),
        admin_routes.criar_blueprint(AdminController(admin_service), auth),
    )
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    return app
