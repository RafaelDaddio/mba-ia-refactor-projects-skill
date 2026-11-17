const { AppError } = require('../utils/errors');
const { isPlainObject, optionalString, requirePositiveInteger, requireString } = require('../utils/validators');

// Campos do contrato: usr, eml, pwd, c_id, card.
function parseCheckout(body) {
  const { usr, eml, pwd, c_id: courseId, card } = isPlainObject(body) ? body : {};
  if (!usr || !eml || !courseId || !card) throw new AppError('Bad Request', 400);

  return {
    name: requireString(usr, 'usr'),
    email: requireString(eml, 'eml'),
    password: optionalString(pwd, 'pwd'),
    courseId: requirePositiveInteger(courseId, 'c_id'),
    card: requireString(card, 'card'),
  };
}

function buildCheckoutController({ checkoutService }) {
  return {
    async create(req, res) {
      const input = parseCheckout(req.body);
      const enrollmentId = await checkoutService.checkout(input, { isAdmin: req.auth.isAdmin });
      res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
  };
}

module.exports = { buildCheckoutController };
