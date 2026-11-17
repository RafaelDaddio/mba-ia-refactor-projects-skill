"""Fluxo das requisições de usuários e do login."""
from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import objeto_json, paginacao


def _textos_preenchidos(*valores):
    return all(isinstance(valor, str) and valor for valor in valores)


class UsuarioController:
    def __init__(self, service, auth):
        self.service = service
        self.auth = auth

    def listar(self):
        limite, offset = paginacao(request.args)
        return jsonify({"dados": self.service.listar(limite, offset), "sucesso": True}), 200

    def buscar_por_id(self, usuario_id):
        self.auth.require_account_owner(usuario_id)
        return jsonify({"dados": self.service.obter(usuario_id), "sucesso": True}), 200

    def criar(self):
        dados = objeto_json(request.get_json(silent=True))
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not _textos_preenchidos(nome, email, senha):
            raise AppError("Nome, email e senha são obrigatórios")

        usuario_id = self.service.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = objeto_json(request.get_json(silent=True), permitir_vazio=True)
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not _textos_preenchidos(email, senha):
            raise AppError("Email e senha são obrigatórios")

        usuario = self.service.autenticar(email, senha)
        token = self.auth.issue_token(usuario["id"], self.service.eh_admin(usuario))
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK", "token": token}), 200
