class EnrollmentModel {
  constructor(db) {
    this.db = db;
  }

  findByUserAndCourse(userId, courseId) {
    return this.db.get(
      'SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?',
      [userId, courseId],
    );
  }

  async create(userId, courseId) {
    const { lastID } = await this.db.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseId],
    );
    return lastID;
  }

  deleteByUser(userId) {
    return this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
  }
}

module.exports = { EnrollmentModel };
