const crypto = require('crypto');
const { AppError } = require('../utils/errors');

const ADMIN_TOKEN_HEADER = 'X-Admin-Token';

const digest = (value) => crypto.createHash('sha256').update(value).digest();
// Compara em tempo constante, sem revelar o tamanho do token esperado.
const safeEqual = (a, b) => crypto.timingSafeEqual(digest(a), digest(b));

/**
 * O projeto não tem login: as provas aceitas são o token administrativo
 * (aqui) e a senha da conta, conferida no service de checkout.
 */
function buildAuth({ adminToken }) {
  const hasAdminToken = (req) => Boolean(adminToken) && safeEqual(req.get(ADMIN_TOKEN_HEADER) || '', adminToken);

  return {
    /** Anota quem pede, para rotas em que a credencial depende do corpo da requisição. */
    identify(req, res, next) {
      req.auth = { isAdmin: hasAdminToken(req) };
      next();
    },

    requireAdmin(req, res, next) {
      next(hasAdminToken(req) ? undefined : new AppError('Autenticação necessária', 401));
    },
  };
}

module.exports = { buildAuth };
