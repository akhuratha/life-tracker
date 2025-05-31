# logging_config.py

import logging
import logging.config

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.DEBUG  # You can set this from an env var


def setup_logging(log_file='app.log'):
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': LOG_FORMAT,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': LOG_LEVEL,
            },
            'file': {
                'class': 'logging.FileHandler',
                'formatter': 'default',
                'filename': log_file,
                'level': LOG_LEVEL,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
        },
    }

    logging.config.dictConfig(logging_config)
