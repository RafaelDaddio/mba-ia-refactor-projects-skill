const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const MEMORY_DATABASE = ':memory:';
const DEFAULT_PORT = 3000;
const DEFAULT_HOST = '127.0.0.1';
const TRUE_VALUES = new Set(['1', 'true', 'yes', 'on']);

// Em todas as leituras, variável definida mas vazia vale como ausente.

function asBoolean(value, fallback) {
  if (!value) return fallback;
  return TRUE_VALUES.has(value.trim().toLowerCase());
}

function asPort(value, fallback) {
  if (!value) return fallback;
  const port = Number(value);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`PORT inválida: ${value}`);
  }
  return port;
}

function resolveDatabasePath(value) {
  if (!value || value === MEMORY_DATABASE) return MEMORY_DATABASE;
  return path.resolve(PROJECT_ROOT, value);
}

function loadConfig(env = process.env) {
  return {
    port: asPort(env.PORT, DEFAULT_PORT),
    host: env.HOST || DEFAULT_HOST,
    databasePath: resolveDatabasePath(env.DATABASE_PATH),
    seedOnStart: asBoolean(env.SEED_ON_START, true),
    // Segredos: sem valor padrão no código.
    adminToken: env.ADMIN_TOKEN || null,
    paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || null,
  };
}

module.exports = { loadConfig };
