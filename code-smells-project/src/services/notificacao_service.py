import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    """Notificações simuladas (e-mail, SMS, push) registradas em log."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação e-mail: pedido %s criado para o usuário %s", pedido_id, usuario_id)
        logger.info("Notificação SMS: pedido %s recebido", pedido_id)
        logger.info("Notificação push: novo pedido %s recebido pelo sistema", pedido_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Notificação: pedido %s aprovado; preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Notificação: pedido %s cancelado; estoque devolvido", pedido_id)
