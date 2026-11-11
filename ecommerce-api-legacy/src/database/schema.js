const { hashPassword } = require('../utils/password');

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    UNIQUE (user_id, course_id)
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL,
    created_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON payments (enrollment_id);
`;

// Dados de exemplo documentados no README: o banco em memória sobe já populado.
const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };
const SEED_COURSES = [
  { title: 'Clean Architecture', price: 997.0 },
  { title: 'Docker', price: 497.0 },
];
const SEED_PAYMENT_STATUS = 'PAID';

async function initSchema(db) {
  await db.exec(SCHEMA);
}

async function seedIfEmpty(db) {
  const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
  if (total > 0) return false;

  const passwordHash = await hashPassword(SEED_USER.password);
  await db.transaction(async () => {
    const user = await db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [SEED_USER.name, SEED_USER.email, passwordHash],
    );
    const courseIds = [];
    for (const course of SEED_COURSES) {
      const { lastID } = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
        [course.title, course.price],
      );
      courseIds.push(lastID);
    }
    const enrollment = await db.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [user.lastID, courseIds[0]],
    );
    await db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollment.lastID, SEED_COURSES[0].price, SEED_PAYMENT_STATUS],
    );
  });
  return true;
}

module.exports = { initSchema, seedIfEmpty };
