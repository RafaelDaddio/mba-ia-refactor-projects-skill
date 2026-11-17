const { PAYMENT_STATUS } = require('../models/paymentModel');

// Regra de aprovação simulada que o projeto sempre usou: cartões com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

const maskCard = (card) => `**** ${card.slice(-VISIBLE_CARD_DIGITS)}`;

class PaymentService {
  constructor({ gatewayKey, logger }) {
    this.gatewayKey = gatewayKey;
    this.logger = logger;
  }

  /** Decide a cobrança e devolve o status do pagamento. */
  charge(card, amount) {
    this.logger.info('Processando pagamento', {
      card: maskCard(card),
      amount,
      gatewayKeyConfigured: Boolean(this.gatewayKey),
    });
    return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  }
}

module.exports = { PaymentService };
