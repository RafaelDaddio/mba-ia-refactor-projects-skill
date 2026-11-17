const { PAYMENT_STATUS } = require('../models/paymentModel');
const { AppError } = require('../utils/errors');
const { hashPassword, verifyPassword } = require('../utils/password');

class CheckoutService {
  constructor({ users, courses, enrollments, payments, auditLogs, paymentService, transaction, logger }) {
    this.users = users;
    this.courses = courses;
    this.enrollments = enrollments;
    this.payments = payments;
    this.auditLogs = auditLogs;
    this.paymentService = paymentService;
    this.transaction = transaction;
    this.logger = logger;
  }

  /**
   * Matricula a conta do e-mail informado no curso e registra o pagamento.
   * E-mail novo cria a conta; e-mail já cadastrado exige a senha da conta ou um administrador.
   */
  async checkout({ name, email, password, courseId, card }, { isAdmin = false } = {}) {
    const account = await this.users.findByEmail(email);
    if (account) await this.assertCanActFor(account, password, isAdmin);

    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new AppError('Curso não encontrado', 404);

    const userId = account ? account.id : await this.register({ name, email, password });
    const enrollmentId = await this.transaction(() => this.enroll(userId, course, card));

    this.logger.info('Checkout concluído', { userId, courseId: course.id, enrollmentId });
    return enrollmentId;
  }

  async assertCanActFor(account, password, isAdmin) {
    if (isAdmin) return;
    if (!password || !(await verifyPassword(password, account.pass))) {
      throw new AppError('Credenciais inválidas', 401);
    }
  }

  async register({ name, email, password }) {
    if (!password) throw new AppError("Campo 'pwd' é obrigatório para criar a conta", 400);
    const passwordHash = await hashPassword(password);
    const userId = await this.users.create({ name, email, passwordHash });
    if (userId === null) throw new AppError('E-mail já cadastrado', 409);
    return userId;
  }

  // Executado dentro de uma transação: matrícula, pagamento e auditoria valem juntos ou não valem.
  async enroll(userId, course, card) {
    if (await this.enrollments.findByUserAndCourse(userId, course.id)) {
      throw new AppError('Usuário já matriculado neste curso', 409);
    }

    const status = this.paymentService.charge(card, course.price);
    if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

    const enrollmentId = await this.enrollments.create(userId, course.id);
    await this.payments.create(enrollmentId, course.price, status);
    await this.auditLogs.record(`Checkout curso ${course.id} por ${userId}`);
    return enrollmentId;
  }
}

module.exports = { CheckoutService };
