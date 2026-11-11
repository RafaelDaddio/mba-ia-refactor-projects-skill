from flask import Blueprint

from controllers import report_controller

bp = Blueprint('reports', __name__)

bp.add_url_rule('/reports/summary', view_func=report_controller.summary_report, methods=['GET'])
bp.add_url_rule('/reports/user/<int:user_id>', view_func=report_controller.user_report, methods=['GET'])
