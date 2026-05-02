import logging
import logging.config
import os
from logging import Handler

from flask import has_request_context, request


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            forwarded_for = request.headers.get("X-Forwarded-For", "")
            real_ip = request.headers.get("X-Real-IP", "")
            if forwarded_for:
                request_ip = forwarded_for.split(",")[0].strip()
            elif real_ip:
                request_ip = real_ip.strip()
            else:
                request_ip = request.remote_addr or "system"

            record.request_ip = request_ip
            record.request_method = request.method
            record.request_path = request.path
        else:
            record.request_ip = "system"
            record.request_method = "-"
            record.request_path = "-"

        return True


class BlockchainLogHandler(Handler):
    def emit(self, record):
        try:
            if not has_request_context():
                return

            from app.services.log_services import LogService

            request_ip = getattr(record, "request_ip", "system")
            request_method = getattr(record, "request_method", "-")
            request_path = getattr(record, "request_path", "-")
            message = record.getMessage()

            if request_method != "-" and request_path != "-":
                message = f"[{request_method} {request_path}] {message}"

            LogService.record_log(message=message, levelno=int(record.levelno), from_ip=request_ip)
        except Exception:
            self.handleError(record)


class ColorFormatter(logging.Formatter):
    levels = {
        logging.DEBUG: "\x1b[34;1m",
        logging.INFO: "\x1b[32;1m",
        logging.WARNING: "\x1b[33;1m",
        logging.ERROR: "\x1b[31;1m",
        logging.CRITICAL: "\x1b[41;1m",
    }
    metadata = "\x1b[36m"
    reset = "\x1b[0m"

    def format(self, record):
        level_color = self.levels.get(record.levelno, self.reset)
        fmt = (
            f"{level_color}%(levelname)s{self.reset} "
            f"{self.metadata}[%(name)s] [%(filename)s] [%(asctime)s]{self.reset} "
            f"%(message)s"
        )
        formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logging(app_name):
    log_dir = "logs"
    log_file = os.path.join(log_dir, "app.log")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_format = "%(levelname)s [%(name)s] [%(filename)s] [%(asctime)s] %(message)s"
    werkzeug_format = "%(levelname)s [%(name)s] %(message)s"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "colored": {
                    "()": ColorFormatter,
                },
                "plain": {"format": file_format, "datefmt": "%Y-%m-%d %H:%M:%S"},
                "werkzeug": {
                    "format": werkzeug_format,
                },
            },
            "handlers": {
                # Handler Console per la tua App (Colorato)
                "console_app": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "colored",
                },
                "file_handler": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file,
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "formatter": "plain",
                    "encoding": "utf8",
                },
                # Handler blockchain per tutti i log applicativi
                "blockchain_handler": {
                    "()": BlockchainLogHandler,
                },
                # Handler Console per Werkzeug (Standard)
                "console_werkzeug": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "werkzeug",  # O quello di default di Werkzeug
                },
            },
            "loggers": {
                app_name: {
                    "level": "DEBUG",
                    "handlers": ["console_app", "file_handler", "blockchain_handler"],
                    "filters": ["request_context"],
                    "propagate": False,
                },
                "werkzeug": {
                    "level": "INFO",
                    "handlers": ["console_werkzeug", "file_handler", "blockchain_handler"],
                    "filters": ["request_context"],
                    "propagate": False,
                },
            },
            "filters": {
                "request_context": {
                    "()": RequestContextFilter,
                }
            },
        }
    )
