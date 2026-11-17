const { hashPassword } = require('../utils/password');

// Conta de exemplo do projeto: a senha é a mesma de antes, agora gravada com hash.
const SAMPLE_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };

/** Insere os dados de exemplo apenas quando o banco ainda não tem usuários nem cursos. */
async function seedIfEmpty(db) {
  const { total } = await db.get(
    'SELECT (SELECT COUNT(*) FROM users) + (SELECT COUNT(*) FROM courses) AS total',
  );
  if (total > 0) return false;

  const passwordHash = await hashPassword(SAMPLE_USER.password);
  await db.transaction(async () => {
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
      SAMPLE_USER.name,
      SAMPLE_USER.email,
      passwordHash,
    ]);
    await db.run(
      "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)",
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
  });
  return true;
}

module.exports = { seedIfEmpty };
