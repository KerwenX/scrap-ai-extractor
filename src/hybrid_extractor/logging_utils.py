import logging
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s request_id=%(request_id)s %(message)s"
    )

    class RequestIdFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "request_id"):
                record.request_id = "-"
            return True

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())

    file_handler = RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())

    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
