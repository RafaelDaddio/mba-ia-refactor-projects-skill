const { AppError } = require('../utils/errors');
const { logger } = require('../utils/logger');

const errorBody = (message) => ({ error: message });

function notFoundHandler(req, res, next) {
  next(new AppError('Rota não encontrada', 404));
}

// Registrado por último: todo erro da aplicação sai no mesmo formato JSON.
function errorHandler(err, req, res, next) {
  if (res.headersSent) return next(err);

  if (err instanceof AppError) return res.status(err.status).json(errorBody(err.message));

  // Erros do parser de corpo do Express (JSON malformado, corpo grande demais).
  if (err.type === 'entity.parse.failed') return res.status(400).json(errorBody('JSON inválido'));
  if (err.expose && err.status >= 400 && err.status < 500) {
    return res.status(err.status).json(errorBody('Requisição inválida'));
  }

  logger.error('Erro inesperado', { method: req.method, path: req.path, error: err.stack });
  return res.status(500).json(errorBody('Erro interno do servidor'));
}

module.exports = { errorHandler, notFoundHandler };
