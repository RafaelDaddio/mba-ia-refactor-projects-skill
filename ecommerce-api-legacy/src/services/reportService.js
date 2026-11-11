const { PAYMENT_STATUS } = require('../models/paymentModel');

const UNKNOWN_STUDENT = 'Unknown';

class ReportService {
  constructor({ reports }) {
    this.reports = reports;
  }

  // Receita e valor pago por aluno consideram só pagamentos PAID.
  async financialReport() {
    const rows = await this.reports.listCourseEnrollments();
    const byCourse = new Map();

    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;

      const entry = byCourse.get(row.course_id);
      const paid = row.payment_status === PAYMENT_STATUS.PAID ? row.payment_amount : 0;
      entry.revenue += paid;
      entry.students.push({
        student: row.user_id === null ? UNKNOWN_STUDENT : row.user_name,
        paid,
      });
    }

    return [...byCourse.values()];
  }
}

module.exports = { ReportService };
