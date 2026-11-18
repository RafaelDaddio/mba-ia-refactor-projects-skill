"""Fluxo das requisições de usuários e do login."""
from flask import jsonify, request

from src.middlewares.auth import emitir_token
from src.utils.errors import AppError
from src.utils.validators import corpo_json, paginacao


def _texto_preenchido(valor):
    return isinstance(valor, str) and bool(valor)


class UsuarioController:
    def __init__(self, usuario_service):
        self.usuarios = usuario_service

    def listar(self):
        limite, offset = paginacao(request.args)
        return jsonify({"dados": self.usuarios.listar(limite, offset), "sucesso": True}), 200

    def buscar_por_id(self, usuario_id):
        return jsonify({"dados": self.usuarios.obter(usuario_id), "sucesso": True}), 200

    def criar(self):
        dados = corpo_json(request)
        nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
        if not all(_texto_preenchido(valor) for valor in (nome, email, senha)):
            raise AppError("Nome, email e senha são obrigatórios", status=400)
        usuario_id = self.usuarios.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = corpo_json(request, obrigatorio=False)
        email, senha = dados.get("email", ""), dados.get("senha", "")
        if not _texto_preenchido(email) or not _texto_preenchido(senha):
            raise AppError("Email e senha são obrigatórios", status=400)
        usuario = self.usuarios.autenticar(email, senha)
        return jsonify({
            "dados": usuario,
            "sucesso": True,
            "mensagem": "Login OK",
            "token": emitir_token(usuario["id"]),  # enviar em `Authorization: Bearer <token>`
        }), 200
