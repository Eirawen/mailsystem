import logging
import sys

from pythonjsonlogger import jsonlogger


def configure_logging(log_level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s %(tenant_id)s %(email_id)s %(provider)s %(event)s %(attempt)s %(latency_ms)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())
