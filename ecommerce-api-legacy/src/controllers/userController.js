const { toPositiveInteger } = require('../utils/validators');

function buildUserController({ userService }) {
  return {
    async delete(req, res) {
      const userId = toPositiveInteger(req.params.id, 'id');
      await userService.delete(userId);
      res.status(200).send('Usuário deletado, junto com suas matrículas e pagamentos.');
    },
  };
}

module.exports = { buildUserController };
