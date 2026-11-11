const { AppError } = require('../utils/errors');

class UserService {
  constructor({ runInTransaction, users, enrollments, payments }) {
    this.runInTransaction = runInTransaction;
    this.users = users;
    this.enrollments = enrollments;
    this.payments = payments;
  }

  // Remove o usuário com as matrículas e os pagamentos dele, sem deixar registros órfãos.
  delete(userId) {
    return this.runInTransaction(async () => {
      const user = await this.users.findById(userId);
      if (!user) throw new AppError('Usuário não encontrado', 404);
      await this.payments.deleteByUser(userId);
      await this.enrollments.deleteByUser(userId);
      await this.users.delete(userId);
    });
  }
}

module.exports = { UserService };
