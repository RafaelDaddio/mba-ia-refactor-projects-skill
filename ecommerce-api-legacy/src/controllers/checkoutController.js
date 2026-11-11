const { validateCheckout } = require('../utils/validators');

function buildCheckoutController({ checkoutService }) {
  return {
    async create(req, res) {
      const input = validateCheckout(req.body);
      const { enrollmentId } = await checkoutService.checkout(input);
      res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
  };
}

module.exports = { buildCheckoutController };
