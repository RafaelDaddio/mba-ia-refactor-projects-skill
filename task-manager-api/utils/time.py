from datetime import datetime, timezone


def utc_now():
    """UTC atual sem fuso, compatível com os valores já gravados no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
