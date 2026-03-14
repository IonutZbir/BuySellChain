import logging
import logging.config
import os


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

    # --- GESTIONE CARTELLA LOG ---
    log_dir = "logs"
    log_file = os.path.join(log_dir, "app.log")

    # Crea la cartella se non esiste
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # -----------------------------

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
                # Handler File per tutto (Senza colori)
                "file_handler": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "plain",
                    "encoding": "utf8",
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
                    "handlers": ["console_app", "file_handler"],
                    "propagate": False,
                },
                "werkzeug": {
                    "level": "INFO",
                    "handlers": ["console_werkzeug", "file_handler"],
                    "propagate": False,
                },
            },
        }
    )
