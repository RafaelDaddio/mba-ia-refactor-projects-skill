// Logger mínimo em JSON por linha. Nunca registre senha, cartão completo ou chaves.
function write(stream, level, msg, meta) {
  stream.write(`${JSON.stringify({ time: new Date().toISOString(), level, msg, ...meta })}\n`);
}

const logger = {
  info: (msg, meta = {}) => write(process.stdout, 'info', msg, meta),
  warn: (msg, meta = {}) => write(process.stderr, 'warn', msg, meta),
  error: (msg, meta = {}) => write(process.stderr, 'error', msg, meta),
};

module.exports = { logger };
