import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

TIPO_PADRAO = "cliente"


class UsuarioService:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self, limite, deslocamento):
        return self.usuarios.listar(limite, deslocamento)

    def obter(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise AppError("Usuário não encontrado", status=404)
        return usuario

    def criar(self, nome, email, senha):
        # O login busca pelo e-mail: duplicatas tornariam a identidade ambígua.
        if self.usuarios.email_cadastrado(email):
            raise AppError("Email já cadastrado", status=409)
        usuario_id = self.usuarios.criar(nome, email, generate_password_hash(senha), TIPO_PADRAO)
        logger.info("Usuário criado com ID %s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        for registro in self.usuarios.listar_credenciais_por_email(email):
            if check_password_hash(registro["senha"] or "", senha):
                logger.info("Login bem-sucedido do usuário %s", registro["id"])
                return {
                    "id": registro["id"],
                    "nome": registro["nome"],
                    "email": registro["email"],
                    "tipo": registro["tipo"],
                }
        logger.info("Tentativa de login recusada")
        raise AppError("Email ou senha inválidos", status=401)
