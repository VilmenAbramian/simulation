from ast import Call
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, NewType, Protocol, Tuple
import logging

from pysim.sim.logger import ModelLogger


EventId = NewType('EventId', int)


# Определения простых сигнатур функций:
Initializer = Callable[["Simulator"], None]
Finalizer = Callable[["Simulator"], object]


class Handler(Protocol):
    """Определение сигнатуры обработчиков событий (более сложный вариант)."""
    def __call__(self, sim: "Simulator", *args: Any) -> None: ...


class SchedulingInPastError(ValueError):
    """Исключение, возникающее при попытке запланировать событие в прошлом."""
    ...


class Simulator:
    """
    Прокси-объект для доступа к контексту и API ядра симуляции из модели.

    Этот объект передается во все обработчики при их вызове ядром.
    Он не содержит функций ядра, которые не нужны обработчикам 
    (например, `run()`), зато может предоставлять более удобные
    сигнатуры (например, `call()`).

    Также симуляция предоставляет общий контекст (поле `context`), 
    доступ к которому есть у всех обработчиков. В качестве контекста
    можно использовать произвольный объект или словарь.
    """

    def __init__(self, kernel: "Kernel", context: object | None = None):
        self._kernel = kernel
        self._context: object = {} if context is None else context
    
    @property
    def context(self) -> object:
        """Получить контекст модели."""
        return self._context
    
    def schedule(
        self,
        delay: float,
        handler: Handler,
        args: Iterable[Any] = (),
        msg: str = ""
    ) -> EventId:
        """Запланировать событие в будущем и вернуть идентификатор события.

        При планировании события нужно указать:
        
        - через какое время оно наступит (`delay`);
        - какую функцию нужно вызвать при наступлении события (`handler`);
        - какие аргументы надо передать функции (`args`).

        Можно также указать строку, которую можно выводить в лог в режиме 
        отладки при наступлении события.

        Args:
            delay (float): интервал времени до наступления события
            handler (Handler): обработчик события
            args (tuple[Any, ...], optional): аргументы для обработчика
            msg (str, optional): комментарий, можно использовать для отладки
        
        Raises:
            SchedulingInPastError: если `delay < 0`
            ValueError: если обработчик не задан (то есть None)
            TypeError: если обработчик не является вызывамым объектом 
                (функцией, функтором), или тип args - не `Iterable`

        Returns:
            EventId: идентификатор события, число больше 0
        """
        return self._kernel.schedule(delay, handler, args, msg)
    
    def call(
        self, 
        handler: Handler,
        args: Iterable[Any] = (),
        msg: str = ""
    ) -> EventId:
        """
        Запланировать событие на текущий момент времени.

        Вариант вызова `schedule()` с `delay = 0`.

        Args:
            handler (Handler): обработчик события
            args (tuple[Any, ...], optional): аргументы для обработчика
            msg (str, optional): комментарий, можно использовать для отладки
        
        Raises:
            ValueError: если обработчик не задан (то есть None)
            TypeError: если обработчик не является вызывамым объектом 
                (функцией, функтором), или тип args - не `Iterable`

        Returns:
            EventId: идентификатор события, число больше 0
        """
        return self._kernel.schedule(0, handler, args, msg)
    
    def cancel(self, event_id: EventId) -> int:
        """
        Отменить событие с идентификатором `event_id`.

        Если событие запланировано в будущем, оно отменяется. То есть,
        когда модельное время достигнет момента его наступления, это событие
        не будет обработано (для оптимизации производительности, сами данные
        события по-прежнему могут храниться где-то в симуляторе).

        Если события с заданным идентификатором не существует, или оно уже
        было отменено, метод ничего не делает и завершается без ошибок.

        Args:
            event_id (EventId): идентификатор события
        
        Retruns:
            int: число отмененных событий
        """
        return self._kernel.cancel(event_id)
    
    def stop(self, msg: str = "") -> None:
        """
        Прекратить выполнение модели.

        Args:
            msg (str): причина остановки, опционально
        """
        self._kernel.stop(msg=msg)
    
    @property
    def time(self) -> float:
        """Получить текущее модельное время."""
        return self._kernel.get_model_time()
    
    @property
    def logger(self) -> ModelLogger:
        """Получить логгер."""
        return self._kernel.logger


class ExitReason(Enum):
    NO_MORE_EVENTS = 0
    REACHED_REAL_TIME_LIMIT = 1
    REACHED_SIM_TIME_LIMIT = 2
    STOPPED = 3


@dataclass
class ExecutionStats:
    num_events_processed: int  # сколько было обработано событий
    sim_time: float            # сколько времени на модельных часах в конце
    time_elapsed: float        # сколько времени длилась симуляция, сек.
    exit_reason: ExitReason    # причина завершения симуляции 
    stop_message: str = ""     # сообщение, переданное в вызов stop()
    last_handler: object | None = None  # последний выполненный обработчик


class Kernel:
    def __init__(self, model_name: str):
        # Настраиваем название модели и логгер
        self._model_name = model_name
        self._logger = ModelLogger(self._model_name)
        self._logger.set_time_getter(self.get_model_time)

        # Объявляем поля, которые потом передаются через сеттеры
        self._initializer: Initializer | None = None
        ...  # TODO: implement
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def logger(self) -> ModelLogger:
        return self._logger

    def schedule(
        self,
        delay: float,
        handler: Handler,
        args: Iterable[Any] = (),
        msg: str = ""
    ) -> EventId:
        return EventId(0)  # TODO: implement
    
    def cancel(self, event_id: EventId) -> int:
        return 0  # TODO: implement
    
    def stop(self, msg: str) -> None:
        ...  # TODO: implement
    
    def get_model_time(self) -> float:
        return 0.0  # TODO: implement
    
    def set_initializer(self, fn: Initializer) -> None:
        self._initializer = fn
        ...  # TODO: implement
    
    def set_finalizer(self, fn: Finalizer) -> None:
        ...  # TODO: implement
    
    def set_context(self, context: object) -> None:
        ...  # TODO: implement

    def get_curr_handler(self) -> object | None:
        """Получить последний вызванный обработчик или инициализатор."""
        ...  # TODO: implement
    
    def set_max_sim_time(self, value: float) -> None:
        ...  # TODO: implement
    
    def set_max_real_time(self, value: float) -> None:
        ...  # TODO: implement
    
    def set_max_num_events(self, value: int) -> None:
        ...  # TODO: implement
    
    def run(self) -> Tuple[ExecutionStats, object, object | None]:
        self._logger.setup()
        self._logger.debug("this is a debug message")
        self._logger.info("this is an info message")
        self._logger.warning("this is a warning message")
        self._logger.error("this is an error message")
        self._logger.critical("this is a critical message")
        print("Just some line")
        if self._initializer:
            self._initializer(Simulator(self))

        # TODO: implement

        # 1) Инициалзировать часы

        # 2) Создать экземпляр Simulator. Если контекст есть,
        #    использовать его. Если нет - использовать словарь (по-умолчанию)

        # 3) Вызвать код инициализации модели

        # 4) Начать выполнение цикла до стоп-условий или опустошения очереди

        # 4.1) Взять очередное неотмененное событие

        # 4.2) Изменить модельное время

        # 4.3) Выполнить обработчик

        # 5) Вызвать код финализации

        return (
            ExecutionStats(
                num_events_processed=0,  # сколько обработали событий
                sim_time=0.0,            # время на модельных часах
                time_elapsed=0.0,        # сколько времени потрачено
                exit_reason=ExitReason.NO_MORE_EVENTS,  # причина выхода
                stop_message="",         # сообщение, если было
                last_handler=self.get_curr_handler(),  # последний обработчик
            ),
            {},  # контекст из объекта Simulator
            None,  # что-то, что вернула функция finalize(), если вызывалась
        )


def simulate(
    model_name: str,
    init: Initializer,
    fin: Finalizer | None = None,
    context: object | None = None,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None
) -> Tuple[ExecutionStats, object, object | None]:
    """
    Запустить симуляцию модели.

    Можно задать несколько условий остановки:
    
    - по реальному времени (сколько секунд до остановки)
    - по модельному времени
    - по числу событий

    Можно задать любое сочетания условий остановки, или ни одного. Модель
    остановится, когда любое из условий будет выполнено.

    Функцию инициализации надо передать обязательно, ее задача - запланировать
    первые события. Функцию финализации можно передавать или не передавать. 
    Если  передать функцию `fin`, то она будет вызвана после завершения 
    симуляции, ее результат будет возвращен в третьем элеменете 
    кортежа-результата.

    Контекст можно передать явно, в виде словаря или объекта (например, 
    некоторого dataclass-а). Если контекст не передать, то он будет 
    инициализирован в пустой словарь. Контекст возвращается во втором
    элементе кортежа-результата.

    Args:
        model_name: название модели
        init: функция инициализации, обязательная
        fin: функция финализации, опциональная
        context: контекст, словарь или объект
        max_real_time: реальное время, по достижении которого надо остановиться
        max_sim_time: модельное время, по достижении которого надо остановиться
        max_num_events: сколько событий обработать до остановки

    Returns:
        stats (ExecutionStats): статистика выполнения модели
        context (object): контекст модели
        fin_ret (object | None): результат вызова finalize(), если был вызов
    """
    # Создаем ядро
    kernel = Kernel(model_name)
    kernel.logger.setup()

    # Настраиваем ядро
    kernel.set_initializer(init)
    if fin is not None:
        kernel.set_finalizer(fin)
    if max_real_time is not None:
        kernel.set_max_real_time(max_real_time)
    if max_sim_time is not None:
        kernel.set_max_sim_time(max_sim_time)
    if max_num_events is not None:
        kernel.set_max_num_events
    
    # Создаем и передаем ядру контекст
    if context is not None:
        kernel.set_context(context)
    else:
        kernel.set_context(None)  # explicit is better than implicit (ZoP:2)
    
    kernel.logger.info("starting kernel %d", 42)

    # Запускаем модель и возвращаем все, что она вернет
    return kernel.run()
