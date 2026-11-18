"""Composition root: cria a aplicação e injeta as dependências de cada camada."""
import logging

from flask import Flask
from flask_cors import CORS

from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database import get_db, init_db
from src.middlewares.auth import init_auth
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.sistema_model import SistemaModel
from src.models.usuario_model import UsuarioModel
from src.routes import register_routes
from src.services.admin_service import AdminService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.sistema_service import SistemaService
from src.services.usuario_service import UsuarioService
from src.utils.logger import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings):
    configure_logging(settings.debug)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DATABASE_PATH=settings.database_path,
        ADMIN_TOKEN=settings.admin_token,
    )
    _avisar_configuracao_ausente(settings)

    CORS(app, origins=settings.cors_origins)
    init_db(app, seed=settings.seed_on_start, senha_admin_seed=settings.seed_admin_password)

    # Models: recebem a função que entrega a conexão da requisição atual.
    produtos = ProdutoModel(get_db)
    usuarios = UsuarioModel(get_db)
    pedidos = PedidoModel(get_db)

    # Services: recebem os models e a configuração de que precisam.
    usuario_service = UsuarioService(usuarios)
    produto_service = ProdutoService(produtos)
    pedido_service = PedidoService(pedidos, produtos, usuarios, NotificacaoService())
    relatorio_service = RelatorioService(pedidos)
    sistema_service = SistemaService(SistemaModel(get_db))
    admin_service = AdminService(AdminModel(get_db), permitir_sql=settings.allow_admin_sql)

    init_auth(app, usuario_service.carregar_para_auth)
    register_routes(
        app,
        produto=ProdutoController(produto_service),
        usuario=UsuarioController(usuario_service),
        pedido=PedidoController(pedido_service),
        relatorio=RelatorioController(relatorio_service),
        sistema=SistemaController(sistema_service),
        admin=AdminController(admin_service),
    )
    register_error_handlers(app)
    return app


def _avisar_configuracao_ausente(settings):
    if settings.secret_key_is_ephemeral:
        logger.warning(
            "SECRET_KEY não definida: usando chave aleatória temporária. "
            "Os tokens de login deixam de valer quando o processo reiniciar."
        )
    if settings.admin_token is None:
        logger.warning(
            "ADMIN_TOKEN não definido: o header X-Admin-Token fica desabilitado; "
            "rotas administrativas aceitam apenas contas com tipo 'admin'."
        )
