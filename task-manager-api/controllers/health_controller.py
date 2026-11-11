"""Endpoints de status da API."""
import datetime

from flask import jsonify

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def health():
    return jsonify({'status': 'ok', 'timestamp': str(datetime.datetime.now())}), 200


def index():
    return jsonify({'message': API_NAME, 'version': API_VERSION}), 200
