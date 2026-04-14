import logging
import os
from logging.handlers import TimedRotatingFileHandler
from flask import Flask

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")


def setup_app_logger(app: Flask) -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)

    log_level = logging.DEBUG if app.config.get("FLASK_ENV") == "development" else logging.INFO
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = TimedRotatingFileHandler(
        os.path.join(_LOG_DIR, "prospect.log"),
        when="midnight", backupCount=14, encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    app.logger.propagate = False
