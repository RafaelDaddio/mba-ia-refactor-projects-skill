const { AsyncLocalStorage } = require('node:async_hooks');
const sqlite3 = require('sqlite3');

/**
 * API em Promises sobre uma conexão sqlite3.
 *
 * A conexão é única e compartilhada, então todo comando passa por uma fila:
 * um comando emitido fora de uma transação espera a transação em andamento
 * terminar e nunca é executado (nem desfeito) dentro da transação de outra
 * requisição.
 */
class Database {
  constructor(raw) {
    this.raw = raw;
    this.queue = Promise.resolve();
    this.transactionScope = new AsyncLocalStorage();
  }

  static async open(databasePath) {
    const db = await new Promise((resolve, reject) => {
      const raw = new sqlite3.Database(databasePath, (err) => (err ? reject(err) : resolve(new Database(raw))));
    });
    await db.exec('PRAGMA foreign_keys = ON');
    return db;
  }

  run(sql, params = []) {
    return this.schedule(() => new Promise((resolve, reject) => {
      this.raw.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    }));
  }

  get(sql, params = []) {
    return this.schedule(() => new Promise((resolve, reject) => {
      this.raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    }));
  }

  all(sql, params = []) {
    return this.schedule(() => new Promise((resolve, reject) => {
      this.raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    }));
  }

  exec(sql) {
    return this.schedule(() => new Promise((resolve, reject) => {
      this.raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    }));
  }

  /** Executa `work` entre BEGIN e COMMIT; qualquer erro faz ROLLBACK e é relançado. */
  transaction(work) {
    if (this.insideTransaction()) return work();
    return this.enqueue(() => this.transactionScope.run(true, async () => {
      await this.exec('BEGIN');
      try {
        const value = await work();
        await this.exec('COMMIT');
        return value;
      } catch (err) {
        await this.exec('ROLLBACK').catch(() => undefined);
        throw err;
      }
    }));
  }

  close() {
    return new Promise((resolve, reject) => {
      this.raw.close((err) => (err ? reject(err) : resolve()));
    });
  }

  insideTransaction() {
    return this.transactionScope.getStore() === true;
  }

  schedule(task) {
    return this.insideTransaction() ? task() : this.enqueue(task);
  }

  enqueue(task) {
    const result = this.queue.then(task);
    this.queue = result.catch(() => undefined);
    return result;
  }
}

module.exports = { Database };
