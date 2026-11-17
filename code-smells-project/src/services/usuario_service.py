"""Regras de negócio de usuários: cadastro, autenticação e dados públicos da conta."""
import logging

from src.utils.errors import AppError
from src.utils.senhas import conferir, gerar_hash

logger = logging.getLogger(__name__)

TIPO_ADMIN = "admin"
TIPO_CLIENTE = "cliente"

_CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
_CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _publico(usuario, campos=_CAMPOS_PUBLICOS):
    """Serialização única da conta: a senha (hash) nunca sai daqui."""
    return {campo: usuario[campo] for campo in campos}


class UsuarioService:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self, limite, offset):
        return [_publico(usuario) for usuario in self.usuarios.listar(limite, offset)]

    def obter(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise AppError("Usuário não encontrado", status=404)
        return _publico(usuario)

    def criar(self, nome, email, senha):
        # O e-mail é a chave de busca do login: não pode se repetir.
        if self.usuarios.buscar_por_email(email) is not None:
            raise AppError("E-mail já cadastrado", status=409)
        usuario_id = self.usuarios.inserir(nome, email, gerar_hash(senha), TIPO_CLIENTE)
        logger.info("Usuário criado: %s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        usuario = self.usuarios.buscar_por_email(email)
        if usuario is None or not conferir(usuario["senha"], senha):
            logger.info("Login falhou")
            raise AppError("Email ou senha inválidos", status=401)
        logger.info("Login bem-sucedido: usuário %s", usuario["id"])
        return _publico(usuario, _CAMPOS_LOGIN)

    @staticmethod
    def eh_admin(usuario):
        return usuario["tipo"] == TIPO_ADMIN
