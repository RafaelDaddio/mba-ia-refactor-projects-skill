const { AppError } = require('../utils/errors');
const { logger } = require('../utils/logger');

function notFoundHandler(req, res, next) {
  next(new AppError('Rota não encontrada', 404));
}

// Registrado por último: todo erro responde em JSON no formato { error: <mensagem> }.
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
  if (err instanceof AppError) {
    return res.status(err.status).json({ error: err.message });
  }
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'JSON inválido' });
  }
  // Erros HTTP do body-parser (corpo grande demais, charset não suportado...).
  if (err.expose && Number.isInteger(err.status) && err.status >= 400 && err.status < 500) {
    return res.status(err.status).json({ error: err.message });
  }
  logger.error('Erro inesperado', { method: req.method, path: req.path, error: err.stack });
  return res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = { errorHandler, notFoundHandler };
