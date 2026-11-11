const sqlite3 = require('sqlite3');

// Conexão SQLite com API em Promises. As transações passam por uma fila,
// para que requisições concorrentes não entrem na mesma transação da conexão compartilhada.
class Database {
  constructor(raw) {
    this.raw = raw;
    this.queue = Promise.resolve();
  }

  static async open(path) {
    const raw = await new Promise((resolve, reject) => {
      const connection = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(connection)));
    });
    const db = new Database(raw);
    await db.exec('PRAGMA foreign_keys = ON');
    return db;
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  exec(sql) {
    return new Promise((resolve, reject) => {
      this.raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
  }

  transaction(work) {
    const result = this.queue.then(async () => {
      await this.exec('BEGIN');
      try {
        const value = await work();
        await this.exec('COMMIT');
        return value;
      } catch (err) {
        await this.exec('ROLLBACK');
        throw err;
      }
    });
    this.queue = result.catch(() => undefined);
    return result;
  }

  close() {
    return new Promise((resolve, reject) => {
      this.raw.close((err) => (err ? reject(err) : resolve()));
    });
  }
}

module.exports = { Database };
