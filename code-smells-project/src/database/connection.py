"""Conexão SQLite por requisição, guardada em `flask.g`."""
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_erro=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()  # transação não confirmada é desfeita
