import logging
import multiprocessing
import sys
import os
import click
import flask
from logging.config import dictConfig
from setting import Conf

log_path = Conf.get_log_path()
TRACE_LOG_LEVEL = 5


class ColourizedFormatter(logging.Formatter):
    level_name_colors = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="blue"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(
            str(level_name), fg="bright_red"
        ),
    }

    def __init__(self, fmt=None, datefmt=None, style="%", use_colors=None):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name, level_no):
        def default(level_name): return str(level_name)
        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def should_use_colors(self):
        return True

    def formatMessage(self, record):
        levelname = record.levelname
        seperator = " " * (8 - len(record.levelname))
        if self.use_colors:
            levelname = self.color_level_name(levelname, record.levelno)
            if "color_message" in record.__dict__:
                record.msg = record.__dict__["color_message"]
                record.__dict__["message"] = record.getMessage()
        record.__dict__["levelprefix"] = levelname + ":" + seperator
        return super().formatMessage(record)


class DefaultFormatter(ColourizedFormatter):
    def should_use_colors(self):
        return sys.stderr.isatty()


class FilterLevel(object):
    def __init__(self, level_name):
        self.level_name = level_name

    def filter(self, record):
        print(record.levelname, self.level_name)
        if record.levelname < self.level_name:
            return False
        else:
            return True


class CustomFormatter(logging.Formatter):

    def format(self, record):
        record.request_id = get_flask_requestid()
        result = super().format(record)
        return result


def get_flask_requestid():
    request_id = ""
    if flask.globals._request_ctx_stack.top is not None:
        request_id = flask.request.headers.get("request_id") or ""
    return request_id


def get_filename(subname):
    subname = subname
    index = ""
    try:
        import uwsgi
        index = uwsgi.worker_id()
    except ImportError:
        process = multiprocessing.current_process()
        if process._identity:
            index = process._identity[0]
    if isinstance(index, int):
        return '{}-{}'.format(subname, index)
    return subname


def set_logger_config(logger_sub_name):
    file_name = get_filename(logger_sub_name)
    formatter_name = "{}.{}".format(CustomFormatter.__module__, CustomFormatter.__qualname__)
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        'incremental': False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] - [%(levelname)s] - [%(filename)s][%(lineno)d] - [%(request_id)s] - %(message)s",
                "class": formatter_name,
            },
            "console": {
                "()": "utils.util_logger.DefaultFormatter",
                "fmt": "%(levelprefix)s - [%(asctime)s] - [%(filename)s][%(lineno)d] - [%(request_id)s] - %(message)s",
                "use_colors": None,
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": os.path.join(log_path, f"{file_name}.log"),
                "when": "MIDNIGHT",
                "backupCount": 14,
                "level": logging.INFO,
                "encoding": "utf-8"
            },
            "console": {
                "formatter": "console",
                "class": "logging.StreamHandler",
                "level": logging.INFO
            },
            "error": {
                "()": "logging.handlers.TimedRotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "default",
                "filename": os.path.join(log_path, f"error-{file_name}.log"),
                "when": "MIDNIGHT",
                "backupCount": 14,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "console"],
                "level": logging.INFO
            },
            "server": {
                "handlers": ["default", "console", "error"],
                "level": logging.INFO,
                "propagate": False
            },
            logger_sub_name: {
                'handlers': ["default", "console", "error"],
                'level': logging.INFO,
                'propagate': False,
            }
        }
    }

    dictConfig(LOGGING_CONFIG)
