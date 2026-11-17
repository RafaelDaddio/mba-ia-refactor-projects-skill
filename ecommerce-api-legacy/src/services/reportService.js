const { PAYMENT_STATUS } = require('../models/paymentModel');

const UNKNOWN_STUDENT = 'Unknown';

class ReportService {
  constructor({ reports }) {
    this.reports = reports;
  }

  /** Por curso: receita dos pagamentos PAID e a lista de alunos com o valor pago. */
  async financialReport() {
    const rows = await this.reports.findEnrollmentsByCourse();
    const byCourse = new Map();

    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;

      const entry = byCourse.get(row.course_id);
      const hasPayment = row.payment_amount !== null;
      if (hasPayment && row.payment_status === PAYMENT_STATUS.PAID) entry.revenue += row.payment_amount;
      entry.students.push({
        student: row.student_name ?? UNKNOWN_STUDENT,
        paid: hasPayment ? row.payment_amount : 0,
      });
    }

    return [...byCourse.values()];
  }
}

module.exports = { ReportService };
