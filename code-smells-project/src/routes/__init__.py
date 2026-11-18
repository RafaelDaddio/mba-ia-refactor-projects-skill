"""Routes (camada View): mapeiam URL e método para os controllers e aplicam o nível de acesso."""
from src.routes import (
    admin_routes,
    pedido_routes,
    produto_routes,
    relatorio_routes,
    sistema_routes,
    usuario_routes,
)


def register_routes(app, produto, usuario, pedido, relatorio, sistema, admin):
    """Registra um blueprint por domínio, cada um com o seu controller."""
    app.register_blueprint(sistema_routes.criar_blueprint(sistema))
    app.register_blueprint(produto_routes.criar_blueprint(produto))
    app.register_blueprint(usuario_routes.criar_blueprint(usuario))
    app.register_blueprint(pedido_routes.criar_blueprint(pedido))
    app.register_blueprint(relatorio_routes.criar_blueprint(relatorio))
    app.register_blueprint(admin_routes.criar_blueprint(admin))
