"""Funções genéricas, sem regra de domínio."""
from datetime import datetime, timezone


def utc_now():
    """UTC atual sem fuso, compatível com os valores já gravados no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
