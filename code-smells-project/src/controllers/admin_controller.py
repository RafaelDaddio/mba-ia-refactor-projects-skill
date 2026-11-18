"""Fluxo das requisições administrativas."""
from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import corpo_json


class AdminController:
    def __init__(self, admin_service):
        self.admin = admin_service

    def reset_database(self):
        self.admin.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        self.admin.exigir_sql_habilitado()  # 403 antes de olhar o corpo
        sql = corpo_json(request, obrigatorio=False).get("sql", "")
        if not isinstance(sql, str) or not sql.strip():
            raise AppError("Query não informada", status=400)

        linhas = self.admin.executar_sql(sql)
        if linhas is not None:
            return jsonify({"dados": linhas, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
