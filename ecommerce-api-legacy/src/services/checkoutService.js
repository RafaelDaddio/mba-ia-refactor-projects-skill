const { AppError } = require('../utils/errors');
const { hashPassword, randomPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../models/paymentModel');

// Gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

const maskCard = (card) => `**** ${card.slice(-VISIBLE_CARD_DIGITS)}`;

function approvePayment(card) {
  return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

class CheckoutService {
  constructor({ runInTransaction, users, courses, enrollments, payments, auditLogs, logger }) {
    this.runInTransaction = runInTransaction;
    this.users = users;
    this.courses = courses;
    this.enrollments = enrollments;
    this.payments = payments;
    this.auditLogs = auditLogs;
    this.logger = logger;
  }

  async checkout({ name, email, password, courseId, card }) {
    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new AppError('Curso não encontrado', 404);

    const userId = await this.findOrCreateUser({ name, email, password });
    const enrollmentId = await this.runInTransaction(() => this.enroll(userId, course, card));
    return { enrollmentId };
  }

  // A conta é criada antes do pagamento, como no fluxo original; busca e criação
  // ficam na mesma transação para que dois checkouts com o mesmo e-mail não dupliquem o usuário.
  findOrCreateUser({ name, email, password }) {
    return this.runInTransaction(async () => {
      const existing = await this.users.findByEmail(email);
      if (existing) return existing.id;
      const passwordHash = await hashPassword(password || randomPassword());
      return this.users.create({ name, email, passwordHash });
    });
  }

  // Executa dentro de uma transação: matrícula, pagamento e auditoria são gravados juntos ou nenhum.
  async enroll(userId, course, card) {
    const alreadyEnrolled = await this.enrollments.findByUserAndCourse(userId, course.id);
    if (alreadyEnrolled) throw new AppError('Aluno já matriculado neste curso', 409);

    this.logger.info('Processando pagamento', { card: maskCard(card), courseId: course.id, userId });
    const status = approvePayment(card);
    if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

    const enrollmentId = await this.enrollments.create(userId, course.id);
    await this.payments.create(enrollmentId, course.price, status);
    await this.auditLogs.create(`Checkout curso ${course.id} por ${userId}`);
    return enrollmentId;
  }
}

module.exports = { CheckoutService };
