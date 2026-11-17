const { requirePositiveInteger } = require('../utils/validators');

function buildUserController({ userService }) {
  return {
    async remove(req, res) {
      await userService.remove(requirePositiveInteger(req.params.id, 'id'));
      res.status(200).send('Usuário deletado.');
    },
  };
}

module.exports = { buildUserController };
