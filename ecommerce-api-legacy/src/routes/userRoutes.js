const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildUserRoutes({ userController }) {
  const router = express.Router();
  router.delete('/users/:id', asyncHandler(userController.delete));
  return router;
}

module.exports = { buildUserRoutes };
