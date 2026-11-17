/** Erro de aplicação: mensagem que pode ir ao cliente + status HTTP. */
class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.name = 'AppError';
    this.status = status;
  }
}

module.exports = { AppError };
