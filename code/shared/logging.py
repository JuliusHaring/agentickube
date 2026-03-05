from logging import getLogger, Logger
from logging.config import dictConfig
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
                "formatter": "default",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
    }
)


def get_logger(name: str) -> Logger:
    return getLogger(name)
