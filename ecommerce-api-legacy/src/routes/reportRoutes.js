const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildReportRoutes({ reportController, adminAuth }) {
  const router = express.Router();
  router.get('/admin/financial-report', adminAuth, asyncHandler(reportController.financialReport));
  return router;
}

module.exports = { buildReportRoutes };
