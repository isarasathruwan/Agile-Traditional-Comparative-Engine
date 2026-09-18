import logging

from app.config.config import settings
from app.config.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(request_id)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)
