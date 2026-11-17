const { AppError } = require('./errors');

const INTEGER_TEXT = /^\d+$/;

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, field) {
  if (typeof value !== 'string' || value === '') {
    throw new AppError(`Campo '${field}' deve ser um texto não vazio`, 400);
  }
  return value;
}

/** Ausente, null ou vazio vira null; qualquer outro valor precisa ser texto. */
function optionalString(value, field) {
  if (value === undefined || value === null || value === '') return null;
  if (typeof value !== 'string') throw new AppError(`Campo '${field}' deve ser um texto`, 400);
  return value;
}

/** Aceita inteiro ou texto só com dígitos (ex.: parâmetro de caminho, "2" num corpo JSON). */
function requirePositiveInteger(value, field) {
  const number = typeof value === 'string' && INTEGER_TEXT.test(value) ? Number(value) : value;
  if (!Number.isSafeInteger(number) || number < 1) {
    throw new AppError(`Campo '${field}' deve ser um inteiro positivo`, 400);
  }
  return number;
}

module.exports = { isPlainObject, requireString, optionalString, requirePositiveInteger };
