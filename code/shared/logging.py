from logging import Logger, getLogger

from colorlog import ColoredFormatter
from pydantic_settings import BaseSettings


class LoggingConfig(BaseSettings):
    log_level: str = "INFO"


_config = LoggingConfig()
LOG_LEVEL = _config.log_level.upper()

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

SECONDARY_COLORS = {
    "message": {
        "DEBUG": "white",
        "INFO": "white",
        "WARNING": "white",
        "ERROR": "white",
        "CRITICAL": "white",
    }
}

DEBUG_FORMAT = (
    "%(log_color)s%(asctime)s "
    "%(cyan)s[%(processName)s:%(process)d]%(reset)s "
    "%(purple)s[%(threadName)s:%(thread)d]%(reset)s "
    "%(log_color)s[%(levelname)s]%(reset)s "
    "%(blue)s%(name)s:%(reset)s "
    "%(message)s"
)

INFO_FORMAT = (
    "%(log_color)s%(asctime)s "
    "%(log_color)s[%(levelname)s]%(reset)s "
    "%(blue)s%(name)s:%(reset)s "
    "%(message)s"
)

LOG_FORMAT = DEBUG_FORMAT if LOG_LEVEL == "DEBUG" else INFO_FORMAT

LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,
            "format": LOG_FORMAT,
            "log_colors": LOG_COLORS,
            "secondary_log_colors": SECONDARY_COLORS,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "colored",
        }
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.error": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
    },
}


def get_logger(name: str) -> Logger:
    return getLogger(name)
