/** Encaminha a rejeição de um handler assíncrono ao middleware de erro. */
const asyncHandler = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);

module.exports = { asyncHandler };
