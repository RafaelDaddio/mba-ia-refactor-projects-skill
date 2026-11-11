const crypto = require('crypto');
const { AppError } = require('../utils/errors');

const ADMIN_TOKEN_HEADER = 'X-Admin-Token';

// Sem ADMIN_TOKEN configurado, nenhuma requisição é aceita nas rotas administrativas.
function adminAuth(adminToken) {
  const expected = Buffer.from(adminToken || '');
  return (req, res, next) => {
    const provided = Buffer.from(req.get(ADMIN_TOKEN_HEADER) || '');
    const authorized = expected.length > 0
      && provided.length === expected.length
      && crypto.timingSafeEqual(provided, expected);
    return authorized ? next() : next(new AppError('Acesso administrativo negado', 401));
  };
}

module.exports = { adminAuth };
