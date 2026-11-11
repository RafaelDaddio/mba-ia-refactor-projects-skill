const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const RANDOM_PASSWORD_BYTES = 32;

// Formato gravado: "<salt hex>:<hash hex>".
async function hashPassword(password) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const derived = await scrypt(password, salt, KEY_LENGTH);
  return `${salt}:${derived.toString('hex')}`;
}

// Senha que ninguém conhece, usada quando a conta é criada sem senha.
function randomPassword() {
  return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('hex');
}

module.exports = { hashPassword, randomPassword };
