const { AppError } = require('./errors');

const INTEGER_TEXT = /^\d+$/;

function requireText(value, field) {
  if (typeof value !== 'string') throw new AppError(`'${field}' deve ser texto`, 400);
  return value;
}

// Aceita inteiro ou inteiro em texto ("2"), como o contrato original aceitava.
function toPositiveInteger(value, field) {
  const number = typeof value === 'string' && INTEGER_TEXT.test(value.trim()) ? Number(value) : value;
  if (!Number.isSafeInteger(number) || number < 1) {
    throw new AppError(`'${field}' deve ser um número inteiro positivo`, 400);
  }
  return number;
}

function validateCheckout(body) {
  const { usr, eml, pwd, c_id: courseId, card } = body && typeof body === 'object' ? body : {};
  // Presença: mesma regra e mensagem do código original.
  if (!usr || !eml || !courseId || !card) throw new AppError('Bad Request', 400);

  return {
    name: requireText(usr, 'usr'),
    email: requireText(eml, 'eml'),
    password: pwd ? requireText(pwd, 'pwd') : null,
    courseId: toPositiveInteger(courseId, 'c_id'),
    card: requireText(card, 'card'),
  };
}

module.exports = { validateCheckout, toPositiveInteger };
