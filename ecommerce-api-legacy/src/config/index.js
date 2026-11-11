const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const IN_MEMORY_DATABASE = ':memory:';

const DEFAULTS = Object.freeze({
  port: 3000,
  host: '127.0.0.1',
  databasePath: IN_MEMORY_DATABASE,
  seedOnStart: true,
});

// Variável definida mas vazia vale como ausente.
function read(env, name) {
  const value = env[name];
  if (value === undefined || value.trim() === '') return null;
  return value.trim();
}

function readBoolean(env, name, fallback) {
  const value = read(env, name);
  if (value === null) return fallback;
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

function readPort(env) {
  const value = read(env, 'PORT');
  if (value === null) return DEFAULTS.port;
  const port = Number(value);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`PORT inválida: ${value}`);
  }
  return port;
}

// Caminhos de arquivo são resolvidos a partir da raiz do projeto, não do diretório de execução.
function readDatabasePath(env) {
  const value = read(env, 'DATABASE_PATH');
  if (value === null || value === IN_MEMORY_DATABASE) return DEFAULTS.databasePath;
  return path.resolve(PROJECT_ROOT, value);
}

function loadConfig(env = process.env) {
  return Object.freeze({
    port: readPort(env),
    host: read(env, 'HOST') || DEFAULTS.host,
    databasePath: readDatabasePath(env),
    seedOnStart: readBoolean(env, 'SEED_ON_START', DEFAULTS.seedOnStart),
    adminToken: read(env, 'ADMIN_TOKEN'),
  });
}

module.exports = { loadConfig };
