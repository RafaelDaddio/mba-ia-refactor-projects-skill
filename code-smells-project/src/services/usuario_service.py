"""Regras de negócio de usuários e autenticação."""
import logging

from src.utils.errors import AppError
from src.utils.senhas import conferir_senha, gerar_hash

logger = logging.getLogger(__name__)

TIPO_ADMIN = "admin"


class UsuarioService:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self, limite, offset):
        return self.usuarios.listar(limite, offset)

    def obter(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise AppError("Usuário não encontrado", status=404)
        return usuario

    def criar(self, nome, email, senha):
        # O e-mail é a chave do login: não pode haver duas contas com o mesmo.
        if self.usuarios.email_existe(email):
            raise AppError("Email já cadastrado", status=409)
        with self.usuarios.transacao():
            usuario_id = self.usuarios.criar(nome, email, gerar_hash(senha))
            if usuario_id is None:  # cadastro concorrente barrado pelo índice único
                raise AppError("Email já cadastrado", status=409)
        logger.info("Usuário criado: id %s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        for candidato in self.usuarios.listar_credenciais_por_email(email):
            if conferir_senha(candidato["senha"], senha):
                logger.info("Login bem-sucedido: usuário %s", candidato["id"])
                return {
                    "id": candidato["id"],
                    "nome": candidato["nome"],
                    "email": candidato["email"],
                    "tipo": candidato["tipo"],
                }
        logger.info("Login falhou")
        raise AppError("Email ou senha inválidos", status=401)

    def carregar_para_auth(self, usuario_id):
        """Conta atual do token: None se não existe mais; o papel é sempre o atual."""
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            return None
        return {"id": usuario["id"], "is_admin": usuario["tipo"] == TIPO_ADMIN}
