from utils.errors import AppError


class AuthService:
    """Login e recarga da conta autenticada a cada requisição."""

    def __init__(self, users):
        self.users = users

    def authenticate(self, email, password):
        user = self.users.find_by_email(email)
        if user is None or not user.check_password(password):
            raise AppError('Credenciais inválidas', status=401)
        if not user.active:
            raise AppError('Usuário inativo', status=403)
        return user

    def load_account(self, user_id):
        """Conta atual do token: None se não existe ou não passaria no login; o papel é o atual."""
        user = self.users.get(user_id)
        if user is None or not user.active:
            return None
        return {'id': user.id, 'is_admin': user.is_admin()}
