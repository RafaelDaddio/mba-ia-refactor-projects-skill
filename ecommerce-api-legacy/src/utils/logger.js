const write = (stream, level, msg, meta) => {
  stream.write(`${JSON.stringify({ time: new Date().toISOString(), level, msg, ...meta })}\n`);
};

// Nunca registre senha, número completo de cartão, token ou chave.
const logger = {
  info: (msg, meta = {}) => write(process.stdout, 'info', msg, meta),
  warn: (msg, meta = {}) => write(process.stderr, 'warn', msg, meta),
  error: (msg, meta = {}) => write(process.stderr, 'error', msg, meta),
};

module.exports = { logger };
