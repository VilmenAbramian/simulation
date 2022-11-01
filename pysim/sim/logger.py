from dataclasses import dataclass
import logging
from turtle import st
from typing import Callable, Literal
import uuid


MODEL_LOGGER_FORMAT = (
    "{modeltime:013.06f} [{levelname:8s}] {name} (R:{runId}) "
    "({filename}:{funcName}) - {message}"
)


class ColoredFormatter(logging.Formatter):
    """
    Logging colored formatter, adapted from 
    https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging
    """

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt, style = '%', **kwargs):
        super().__init__(fmt=fmt, style=style, **kwargs)  # type: ignore
        self.fmt = fmt
        self.style = style
        self.FORMATS = {
            logging.DEBUG: logging.Formatter(
                self.grey + self.fmt + self.reset, 
                style=style  # type: ignore
            ),
            logging.INFO: logging.Formatter(
                self.blue + self.fmt + self.reset,
                style=style  # type: ignore
            ),
            logging.WARNING: logging.Formatter(
                self.yellow + self.fmt + self.reset,
                style=style  # type: ignore
            ),
            logging.ERROR: logging.Formatter(
                self.red + self.fmt + self.reset,
                style=style  # type: ignore
            ),
            logging.CRITICAL: logging.Formatter(
                self.bold_red + self.fmt + self.reset,
                style=style  # type: ignore
            ),
        }

    def format(self, record):
        log_fmt: logging.Formatter = self.FORMATS[record.levelno]
        return log_fmt.format(record)


@dataclass
class ModelLoggerConfig:
    fmt: str = MODEL_LOGGER_FORMAT
    style: str = '{'



class ModelLogger:
    def __init__(self, model_name: str = ""):
        self._logger = logging.getLogger(model_name)
        self.time_getter = lambda: 0
        self.__was_set_up = False
        self._run_id: int = uuid.uuid4().int % 1_000_000
    
    def set_time_getter(self, fn: Callable[[], float]):
        self.time_getter = fn
    
    def set_run_id(self, run_id: int):
        self._run_id = run_id
    
    def setup(
        self, 
        fmt: str = MODEL_LOGGER_FORMAT, 
        style: str = '{',
        level: int = logging.DEBUG,
        use_console: bool = True,
        console_level: int = 0,
        file_name: str | None = None,
        file_mode: Literal['w', 'a'] = 'a',
        file_level: int = 0,
    ):
        if not self.__was_set_up:
            c_formatter = ColoredFormatter(MODEL_LOGGER_FORMAT, style='{')
            f_formatter = logging.Formatter(MODEL_LOGGER_FORMAT, style='{')

            if use_console:                
                s_handler = logging.StreamHandler()
                s_handler.setLevel(console_level or level)                
                s_handler.setFormatter(c_formatter)
                self._logger.addHandler(s_handler)

            if file_name is not None:                                
                f_handler = logging.FileHandler(file_name, mode = file_mode)
                f_handler.setLevel(file_level or level)
                f_handler.setFormatter(f_formatter)
                self._logger.addHandler(f_handler)

            self._logger.propagate = False
            self._logger.setLevel(level)
            self.__was_set_up = True
    
    def _get_extra(self):
        return {
            "modeltime": self.time_getter(),
            "runId": self._run_id,
        }

    def debug(self, msg, *args, **kwargs):
        self._logger.debug(
            msg, *args, **kwargs, 
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )

    def info(self, msg, *args, **kwargs):
        self._logger.info(
            msg, *args, **kwargs, 
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )
    
    def warning(self, msg, *args, **kwargs):
        self._logger.warning(
            msg, *args, **kwargs, 
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )
    
    def error(self, msg, *args, **kwargs):
        self._logger.error(
            msg, *args, **kwargs,
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )
    
    def critical(self, msg, *args, **kwargs):
        self._logger.critical(
            msg, *args, **kwargs,
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )

    def log(self, level: int, msg, *args, **kwargs):
        self._logger.log(
            level, msg, *args, **kwargs,
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )
