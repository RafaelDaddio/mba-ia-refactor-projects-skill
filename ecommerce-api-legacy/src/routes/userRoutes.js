const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function buildUserRoutes({ userController, auth }) {
  const router = express.Router();
  // Nível "dono da conta ou administrador". Sem login no projeto e sem senha
  // nesta rota, a única prova disponível é o token administrativo.
  router.delete('/users/:id', auth.requireAdmin, asyncHandler(userController.remove));
  return router;
}

module.exports = { buildUserRoutes };
