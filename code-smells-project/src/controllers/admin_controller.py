from flask import jsonify, request

from src.utils.errors import AppError
from src.utils.validators import exigir_objeto


class AdminController:
    def __init__(self, service):
        self.service = service

    def resetar_banco(self):
        self.service.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def executar_query(self):
        dados = exigir_objeto(request.get_json(silent=True), permitir_vazio=True)
        sql = dados.get("sql", "")
        if not sql or not isinstance(sql, str):
            raise AppError("Query não informada")
        linhas = self.service.executar_sql(sql)
        if linhas is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": linhas, "sucesso": True}), 200
