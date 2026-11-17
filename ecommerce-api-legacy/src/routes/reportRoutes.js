const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildReportRoutes({ reportController, auth }) {
  const router = express.Router();
  router.get('/admin/financial-report', auth.requireAdmin, asyncHandler(reportController.financial));
  return router;
}

module.exports = { buildReportRoutes };
