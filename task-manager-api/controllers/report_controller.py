from flask import jsonify


class ReportController:
    def __init__(self, report_service):
        self.reports = report_service

    def summary_report(self):
        return jsonify(self.reports.summary()), 200

    def user_report(self, user_id):
        return jsonify(self.reports.user_report(user_id)), 200
