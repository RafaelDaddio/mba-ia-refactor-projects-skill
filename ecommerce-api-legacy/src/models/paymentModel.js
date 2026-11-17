// Mesmos valores do CHECK da tabela payments (database/schema.js).
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

class PaymentModel {
  constructor(db) {
    this.db = db;
  }

  create(enrollmentId, amount, status) {
    return this.db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
      enrollmentId,
      amount,
      status,
    ]);
  }

  deleteByUserId(userId) {
    return this.db.run(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [userId],
    );
  }
}

module.exports = { PaymentModel, PAYMENT_STATUS };
