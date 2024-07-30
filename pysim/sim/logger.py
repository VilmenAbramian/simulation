from dataclasses import dataclass
import logging
from typing import Callable, Literal
import uuid
import colorama


class ColoredFormatter(logging.Formatter):
    """
    Форматтер, выводит записи лога в консоль цветом, зависящим от уровня.

    Основа кода взята отсюда:
    https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging
    """

    # Цвета по-умолчанию
    DEFAULT_COLORS = {
        logging.DEBUG: colorama.Fore.LIGHTBLACK_EX,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARN: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED + colorama.Style.BRIGHT,
        logging.CRITICAL:
            colorama.Back.RED + colorama.Fore.WHITE + colorama.Style.BRIGHT,
    }

    def __init__(
        self, 
        fmt: str, 
        style: Literal['{', '%', '$'] = '%', 
        colors: dict[int, str] | None = None,
        **kwargs
    ):
        super().__init__(fmt=fmt, style=style, **kwargs)  # type: ignore
        colors = colors or {}  # Если colors = None, то присвоить {} 
        self.FORMATS = {
            level: logging.Formatter(
                colors.get(level, ColoredFormatter.DEFAULT_COLORS[level]) +
                fmt + colorama.Style.RESET_ALL,
                style=style  # type: ignore
            )
            for level in ColoredFormatter.DEFAULT_COLORS.keys()
        }

    def format(self, record):
        log_fmt: logging.Formatter = self.FORMATS[record.levelno]
        return log_fmt.format(record)


# Формат вывода по-умолчанию. Используются часть стандартных полей,
# а также два дополнительных, которые добавляются классом ModelLogger:
#
# - simTime: модельное время
# - runId: идентификатор запуска модели
#
# Пример строки в журнале:
# 000123.456000 [DEBUG   ] model (R:972274) (simulator.py:run) - a message

MODEL_LOGGER_FORMAT = (
    "{simTime:013.06f} [{levelname:8s}] {name} (R:{runId}) "
    "({filename}:{funcName}) - {message}"
)


@dataclass
class ModelLoggerConfig:
    """Настройки модельного логгера."""
    fmt: str = MODEL_LOGGER_FORMAT       # формат-строка логгера
    style: Literal['%', '{', '$'] = '{'  # стиль формат-строки логгера
    
    level: int = logging.DEBUG     # уровень логгирования по-умолчанию
    
    use_console: bool = False      # логгировать ли в консоль
    colored_console: bool = True  # использовать ли цветной вывод в консоль

    # Кастомные цвета (ключ - уровень логгирования, значение - цвет).
    # Если не заданы, используются значения по-умолчанию из ColoredFormatter.
    console_colors: dict[int, str] | None = None

    # Уровень логгирования в консоль, если не задан - использовать level
    console_level: int = 0

    # Имя лог-файла (без runId). Если не задан, логгирования в файл не будет.
    file_name: str | None = 'results/logs/RFIDlog.txt'
    
    # Уровень логгирования в файл, если не задан - использовать level
    file_level: int = 0
    
    # Разделитель между именем файла и runId (file_name<SEP>runId.log)
    file_name_sep: str = "_"

    # Формировать имя файла без run_id. Удобно для отладки модели.
    file_name_no_run_id: bool = False


class ModelLogger:
    """
    Логгер для моделей.

    В дополнение к стандартному логгеру, предоставляет дополнительные поля
    к строке формата:

    - simTime: модельное время
    - runId: идентификатор запуска модели (уникальный номер)

    Проксирует вызовы записи в лог (debug, info, warning, error, critical,
    log, exception), добавляет новые поля. В качестве имени логгера использует
    название модели, которое передается в конструкторе.

    Для повышения производительности желательно передавать сообщения в лог
    не в виде сформированной строки, а через формат-строку. То есть вместо

        `debug(f"variable = {value_of_x}")` 

    использовать вызов 

        `debug("variable = %d", value_of_x)`
    
    В первом случае строка будет строиться независимо от того, будет ли это
    сообщение выводиться в лог (например, если уровень логгирования - WARNING).
    Во втором случае строка будет формироваться только при реальной записи
    в журнал.

    Конфигурирование логгера производится в методе `setup()`, все параметры
    передаются через объект типа `ModelLoggerConfig`. 

    Если включена запись в файл с именем "logname.log", реально будет
    записывать в файл с именем "logname_<runId>.log". Имя файла можно задать
    без ".log", тогда идентификатор запуска будет просто добавлен в конце.
    Вывод в консоль по-умолчанию делает цветным, используя ColoredFormatter.
    """
    def __init__(
        self, 
        model_name: str = '', 
        time_getter: Callable[[], float] | None = None,
        run_id: int | None = None
    ):
        """Конструктор.

        Args:
            model_name: название модели
            time_getter: функция получения модельного времени
            run_id: идентификатор запуска
        """
        self._logger = logging.getLogger(model_name)
        self.time_getter = time_getter or (lambda: 0)
        self._run_id: int = run_id or uuid.uuid4().int % 1_000_000
        self._setup_was_called: bool = False
    
    def set_time_getter(self, fn: Callable[[], float]) -> None:
        """Настроить функцию получения модельного времени."""
        self.time_getter = fn
    
    def set_run_id(self, run_id: int) -> None:
        self._run_id = run_id
    
    def setup(
        self, 
        config: ModelLoggerConfig | None = None, 
        force_run: bool = False
    ) -> None:
        """
        Настроить логгер.

        По-умолчанию, повторные вызовы метода setup() игнорируются. Причина:
        в коде запуска ядра есть вызов `setup()` с параметрами по-умолчанию. 
        Он должен происходить, если ранее логгер не был настроен явно,
        с кастомной конфигурацией.

        Можно заставить метод выполниться повторно, передав force_run = True.

        Args:
            config (ModelLoggerConfig): конфигурация логгера
            force_run (bool): выполнить, даже если ранее логгер был настроен
        """
        if self._setup_was_called and not force_run:
            return
        
        config = config or ModelLoggerConfig()
        self._logger.handlers = []
        if config.use_console:
            if config.colored_console:
                c_formatter = ColoredFormatter(
                    config.fmt, 
                    style=config.style,
                    colors=config.console_colors
                )
            else:
                c_formatter = logging.Formatter(config.fmt, style=config.style)
            s_handler = logging.StreamHandler()
            s_handler.setLevel(config.console_level or config.level)     
            s_handler.setFormatter(c_formatter)
            self._logger.addHandler(s_handler)

        if config.file_name is not None:
            f_formatter = logging.Formatter(config.fmt, style=config.style)
            
            # Строим имя файла
            if config.file_name_no_run_id:
                file_name = config.file_name
            else:
                file_name = ModelLogger.build_file_name(
                    config.file_name, 
                    self._run_id
                )
            
            # Каждый запуск создает отдельный файл, поэтому режим = 'w'
            f_handler = logging.FileHandler(file_name,  mode = 'w')
            f_handler.setLevel(config.file_level or config.level)
            f_handler.setFormatter(f_formatter)
            self._logger.addHandler(f_handler)

        self._logger.propagate = False
        self._logger.setLevel(config.level)
        
        # Отменчаем, что настройка была выполнена.
        self._setup_was_called = True
    
    def _get_extra(self):
        return {
            "simTime": self.time_getter(),
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
    
    def exception(self, msg, *args, **kwargs):
        self._logger.exception(
            msg, *args, **kwargs,
            extra=self._get_extra(),
            stacklevel=2,  # skip this (ModelLogger.xxx()) function
        )
    
    @staticmethod
    def build_file_name(file_name: str, run_id: int, sep: str = "_"):
        """Построить имя файла.
        
        Если file_name имеет вид "something.log", а run_id равен 123, 
        то результат будет "something_123.log".
        
        Если file_name имеет вид "something" (без расширения), то результат
        будет "something_123". Если расширение есть, но не равно "log",
        то оно не считается (то есть будет "something.ext_123").
        """
        file_name = file_name.strip()
        ext_pos = file_name.rfind('.')
        if ext_pos >= 0 and file_name[ext_pos+1:].lower() == "log":
            return file_name[:ext_pos] + sep + str(run_id) + file_name[ext_pos:]
        return file_name + sep + str(run_id)
