const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildCheckoutRoutes({ checkoutController }) {
  const router = express.Router();
  router.post('/checkout', asyncHandler(checkoutController.create));
  return router;
}

module.exports = { buildCheckoutRoutes };
