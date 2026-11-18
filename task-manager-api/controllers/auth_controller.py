from flask import jsonify, request

from middlewares.auth import issue_token
from utils.errors import AppError
from utils.validators import INVALID_BODY_MESSAGE, json_body


class AuthController:
    def __init__(self, auth_service):
        self.auth = auth_service

    def login(self):
        data = json_body(request)
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            raise AppError('Email e senha são obrigatórios', status=400)
        if not isinstance(email, str) or not isinstance(password, str):
            raise AppError(INVALID_BODY_MESSAGE, status=400)

        user = self.auth.authenticate(email, password)
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': issue_token(user.id),
        }), 200
