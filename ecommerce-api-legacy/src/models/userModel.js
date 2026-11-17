class UserModel {
  constructor(db) {
    this.db = db;
  }

  findById(id) {
    return this.db.get('SELECT id, name, email, pass FROM users WHERE id = ?', [id]);
  }

  findByEmail(email) {
    return this.db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
  }

  /** Devolve o id da nova conta, ou null se o e-mail já estiver cadastrado. */
  async create({ name, email, passwordHash }) {
    const { lastID, changes } = await this.db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?) ON CONFLICT (email) DO NOTHING',
      [name, email, passwordHash],
    );
    return changes > 0 ? lastID : null;
  }

  deleteById(id) {
    return this.db.run('DELETE FROM users WHERE id = ?', [id]);
  }
}

module.exports = { UserModel };
