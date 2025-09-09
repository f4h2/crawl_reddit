# import logging
# import logging.config
# from pythonjsonlogger import jsonlogger  # pip install python-json-logger
# import os
#
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
#
# def setup_logging():
#     formatter = {
#         "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
#     }
#
#     logging_config = {
#         "version": 1,
#         "disable_existing_loggers": False,
#
#         "formatters": {
#             "json": {
#                 "()": jsonlogger.JsonFormatter,
#                 **formatter
#             },
#             "standard": {
#                 "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#             }
#         },
#
#         "handlers": {
#             "console": {
#                 "class": "logging.StreamHandler",
#                 "formatter": "standard",
#                 "level": LOG_LEVEL,
#             },
#             "file": {
#                 "class": "logging.handlers.RotatingFileHandler",
#                 "filename": LOG_FILE,
#                 "formatter": "json",
#                 "maxBytes": 5 * 1024 * 1024,  # 5MB
#                 "backupCount": 5,
#                 "level": LOG_LEVEL,
#             }
#         },
#
#         "root": {
#             "handlers": ["console", "file"],
#             "level": LOG_LEVEL,
#         }
#     }
#
#     logging.config.dictConfig(logging_config)


import logging
import logging.config
from pythonjsonlogger import jsonlogger  # pip install python-json-logger
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logging():
    formatter = {
        "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
    }

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                **formatter
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": LOG_LEVEL,
            }
        },

        "root": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        }
    }

    logging.config.dictConfig(logging_config)
