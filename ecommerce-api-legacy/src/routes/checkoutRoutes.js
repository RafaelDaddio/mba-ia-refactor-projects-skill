const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildCheckoutRoutes({ checkoutController, auth }) {
  const router = express.Router();
  // E-mail novo: pública (cadastro). E-mail já cadastrado: senha da conta ou token administrativo.
  router.post('/checkout', auth.identify, asyncHandler(checkoutController.create));
  return router;
}

module.exports = { buildCheckoutRoutes };
