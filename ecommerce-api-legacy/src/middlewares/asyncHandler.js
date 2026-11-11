// Encaminha rejeições de handlers assíncronos ao middleware de erro.
const asyncHandler = (handler) => (req, res, next) => (
  Promise.resolve(handler(req, res, next)).catch(next)
);

module.exports = { asyncHandler };
