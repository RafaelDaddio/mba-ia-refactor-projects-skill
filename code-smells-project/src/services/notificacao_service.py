"""Notificações de pedidos (simuladas com logging, como no projeto original)."""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def pedido_aprovado(self, pedido_id):
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Estoque devolvido.", pedido_id)
