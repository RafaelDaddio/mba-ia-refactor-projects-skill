"""Composition root: cria a aplicação e injeta as dependências de cada camada."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import registrar_tratamento_de_erros
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
from src.services.health_service import HealthService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.utils.logger import configurar_logging

logger = logging.getLogger(__name__)


def create_app(settings):
    configurar_logging(settings.debug)
    if settings.secret_key_temporaria:
        logger.warning("SECRET_KEY não definida: usando chave aleatória temporária.")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DATABASE_PATH=settings.database_path,
        ADMIN_TOKEN=settings.admin_token,
        ALLOW_ADMIN_SQL=settings.allow_admin_sql,
    )
    CORS(app, origins=settings.cors_origins)
    database.init_db(app, seed=settings.seed_on_start, senha_admin=settings.seed_admin_password)
    registrar_tratamento_de_erros(app)

    # Models recebem a função que devolve a conexão da requisição atual.
    produtos = ProdutoModel(database.get_db)
    usuarios = UsuarioModel(database.get_db)
    pedidos = PedidoModel(database.get_db)
    admin = AdminModel(database.get_db)

    produto_service = ProdutoService(produtos)
    usuario_service = UsuarioService(usuarios)
    pedido_service = PedidoService(pedidos, produtos, usuarios, NotificacaoService())
    relatorio_service = RelatorioService(pedidos)
    admin_service = AdminService(admin)
    health_service = HealthService(produtos, usuarios, pedidos)

    for blueprint in (
        sistema_routes.criar_blueprint(SistemaController(health_service, settings.versao_api)),
        produto_routes.criar_blueprint(ProdutoController(produto_service)),
        usuario_routes.criar_blueprint(UsuarioController(usuario_service)),
        pedido_routes.criar_blueprint(PedidoController(pedido_service)),
        relatorio_routes.criar_blueprint(RelatorioController(relatorio_service)),
        admin_routes.criar_blueprint(AdminController(admin_service)),
    ):
        app.register_blueprint(blueprint)
    return app
