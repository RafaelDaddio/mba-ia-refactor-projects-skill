from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import exigir_objeto, paginacao


class UsuarioController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        limite, deslocamento = paginacao(request.args.get("limit"), request.args.get("offset"))
        return jsonify({"dados": self.service.listar(limite, deslocamento), "sucesso": True}), 200

    def obter(self, usuario_id):
        return jsonify({"dados": self.service.obter(usuario_id), "sucesso": True}), 200

    def criar(self):
        dados = exigir_objeto(request.get_json(silent=True))
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise AppError("Nome, email e senha são obrigatórios")
        if not all(isinstance(valor, str) for valor in (nome, email, senha)):
            raise AppError("Nome, email e senha devem ser textos")
        usuario_id = self.service.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = exigir_objeto(request.get_json(silent=True), permitir_vazio=True)
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            raise AppError("Email e senha são obrigatórios")
        if not isinstance(email, str) or not isinstance(senha, str):
            raise AppError("Email e senha devem ser textos")
        usuario = self.service.autenticar(email, senha)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
