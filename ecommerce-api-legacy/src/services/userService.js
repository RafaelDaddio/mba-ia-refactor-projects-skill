const { AppError } = require('../utils/errors');

class UserService {
  constructor({ users, enrollments, payments, transaction }) {
    this.users = users;
    this.enrollments = enrollments;
    this.payments = payments;
    this.transaction = transaction;
  }

  /** Exclui a conta com as matrículas e os pagamentos dela, sem deixar registros órfãos. */
  remove(userId) {
    return this.transaction(async () => {
      if (!(await this.users.findById(userId))) throw new AppError('Usuário não encontrado', 404);
      await this.payments.deleteByUserId(userId);
      await this.enrollments.deleteByUserId(userId);
      await this.users.deleteById(userId);
    });
  }
}

module.exports = { UserService };
