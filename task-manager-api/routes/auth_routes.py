from flask import Blueprint


def create_blueprint(controller):
    bp = Blueprint('auth', __name__)
    bp.add_url_rule('/login', view_func=controller.login, methods=['POST'])
    return bp
