"""Fluxo HTTP de /reports."""
from flask import jsonify

from models.category import Category
from models.task import Task
from models.user import User
from services.report_service import ReportService


def _service():
    return ReportService(tasks=Task, users=User, categories=Category)


def summary_report():
    return jsonify(_service().summary()), 200


def user_report(user_id):
    return jsonify(_service().user_report(user_id)), 200
