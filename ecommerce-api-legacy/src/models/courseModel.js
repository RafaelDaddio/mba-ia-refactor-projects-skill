const ACTIVE = 1;

class CourseModel {
  constructor(db) {
    this.db = db;
  }

  findActiveById(id) {
    return this.db.get(
      'SELECT id, title, price, active FROM courses WHERE id = ? AND active = ?',
      [id, ACTIVE],
    );
  }
}

module.exports = { CourseModel };
