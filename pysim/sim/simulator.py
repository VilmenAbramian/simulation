from dataclasses import dataclass
from enum import Enum
import heapq
import itertools
import time
from typing import Any, Callable, Iterable, NewType, Tuple, Iterator

from pysim.sim.logger import ModelLogger, ModelLoggerConfig


EventId = NewType('EventId', int)

# Определения простых сигнатур функций:
Finalizer = Callable[["Simulator"], object]
Initializer = Callable[["Simulator", ...], None]
Handler = Callable[["Simulator", ...], None]


class SchedulingInPastError(ValueError):
    """Исключение, возникающее при попытке запланировать событие в прошлом."""
    ...


class ExitReason(Enum):
    NO_MORE_EVENTS = 0
    REACHED_REAL_TIME_LIMIT = 1
    REACHED_SIM_TIME_LIMIT = 2
    STOPPED = 3
    INTERRUPTED = 4  # выполнение не закончилось - прерывание при отладке


@dataclass
class ExecutionStats:
    '''
    Структура дынных для хранения результатов
    исполнения одного "прогона" симулятора
    Some args:
        sim_time - временя на модельных часах (после выполнения)
        time_elapsed - длительность симуляции в секундах
        last_handler - последний выполненный обработчик и его аргументы
        last_sim_time - для режима отладки: предыдущий момент времени
    '''
    num_events_processed: int
    sim_time: float
    time_elapsed: float
    exit_reason: ExitReason
    stop_message: str = ""
    last_handler: tuple[Handler, tuple[...]] | None = None
    next_handler: tuple[Handler, tuple[...]] | None = None
    last_sim_time: float = 0


ExecResult = Tuple[ExecutionStats, object | dict, object | dict | None]


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
        self._context: object | dict = {} if context is None else context

    @property
    def context(self) -> object | dict:
        """Получить контекст модели."""
        return self._context

    @context.setter
    def context(self, ctx: object | dict) -> None:
        """Назначить контекст."""
        self._context = ctx

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
            TypeError: если обработчик не является вызываемым объектом
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


class EventQueue:
    '''
    Очередь событий, реализованная с помощью
    струкртуры данных "приоритетная куча (heapq)"
    '''
    def __init__(self):
        '''
        Args:
            _event_list - лист событий, который будет упорядочен,
                как приоритетная минимальная куча
            _event_dict -  словарь, сопоставляющий задачи с записями в листе
            _next_id - уникальный порядковый номер события
            removed - Заполнитель для удалённого события (можно взамен использовать None)
        '''
        self._event_list = []
        self._event_dict = {}
        self._next_id = itertools.count()
        # self.removed = '<removed-task>'

    def push(self, time, task):
        '''
        Добавление нового события по правилам кучи

        Args:
        time - число (int, float), характеризующее время (приоритет) события
        task - string, текстовое название события

        Returns:
        event_id - уникальный порядковый номер события

        Куча - это list, но отсортированный, исходя из правил наименьшего
        бинарного дерева. Здесь нет преобразования данных list по правилам кучи,
        потому что list изначально пуст и события в него добавляются сразу же
        исходя из правил кучи
        '''
        event_id = next(self._next_id)  # Генерируем уникальный номер события
        event = [time, event_id, task]  # Формируем list события
        self._event_dict[event_id] = event
        heapq.heappush(self._event_list, event)
        return event_id

    def pop(self):
        '''
        :raises:
            - KeyError: если очередь пуста
        '''
        if self.empty:
            raise KeyError("Pop из пустой очереди событий!")
        (time, event_id, task) = heapq.heappop(self._event_list)
        while task is None:
            (time, event_id, task) = heapq.heappop(self._event_list)
        self._event_dict.pop(event_id)
        return time, event_id, task

    def __len__(self):
        '''
        Количество событий в очереди
        '''
        return len(self._event_dict)

    def cancel(self, event_id):
        '''
        Отмена запланированного события в будущем
        '''
        if event_id in self._event_dict and event_id is not None:
            event = self._event_dict.pop(event_id)  # Удаляем запись о событии из словаря (но не из кучи)
            event[-1] = None
            return (event)

    def clear(self):
        '''
        Очистка очереди событий
        '''
        self._event_list.clear()
        self._event_dict.clear()

    @property
    def empty(self):
        return len(self._event_dict) == 0

    def to_list(self):
        return list(self._event_list)


class Kernel:
    '''
    Some args:
        _sim_time - модельное время (в условных единицах)
        _t_start - Реальное время начала симуляции
        _max_sim_time - пользовательское максимальное виртуальное время симуляции
        _max_real_time - пользовательское максимальное реальное время симуляции
        _max_num_events - пользовательское максимальное количество обслуживаемых событий
        lhandler - последний исполненный обработчик
    '''
    def __init__(self, model_name: str):
        # Настраиваем название модели и логгер
        self._model_name = model_name
        self._logger = ModelLogger(self._model_name)
        self._logger.set_time_getter(self.get_model_time)

        # Объявляем поля, которые потом передаются через сеттеры
        self._initializer: Initializer | None = None
        self._initializer_args: Iterable[Any] = ()

        # Очередь событий
        self._queue = EventQueue()

        # Время и часы
        self._sim_time = 0.0
        self._t_start = None
        self._max_sim_time = None
        self._max_real_time = None

        # Прочее
        self.context = None
        self._debug = False
        self._user_stop = False
        self.stop_reason = None
        self.stop_msg = ''
        self._num_events_served = None
        self._max_num_events = None

        self.lhandler = None
        self._finalize = None

        # self._state = self.State.READY

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def logger(self) -> ModelLogger:
        return self._logger

    @property
    def debug(self) -> bool:
        return self._debug

    def set_debug(self, value: bool):
        if value != self._debug:
            if value:
                self.logger.info("Enter debugger mode")
            else:
                self.logger.info("Exit debugger mode")
            self._debug = value

    def schedule(
            self,
            delay: float,
            handler: Handler,
            args: Iterable[Any] = (),
            msg: str = ""
    ) -> EventId:
        '''Планирование нового события'''
        if delay is not None:
            return self._queue.push(self._sim_time + delay, (handler, args, msg))
        return None

    def cancel(self, event_id: EventId) -> int:
        '''Отменить событие с идентификатором `event_id`'''
        if event_id in self._queue._event_dict:
            self._queue.cancel(event_id)
            return 1
        return 0

    def stop(self, msg: str) -> None:
        self.stop_reason = ExitReason.STOPPED
        self._user_stop = True
        self.stop_msg = msg
        self.logger.debug(f'Симуляция остановлена с сообщением {msg}')

    def stop_conditions(self, msg: str = None) -> bool:
        '''Возвращает True для остановки модели'''
        if self._max_sim_time is not None and self._sim_time > self._max_sim_time:
            self.stop_reason = ExitReason.REACHED_SIM_TIME_LIMIT
            return True
        elif self._max_real_time is not None and self.real_time_elapsed > self._max_real_time:
            self.stop_reason = ExitReason.REACHED_REAL_TIME_LIMIT
            return True
        elif self._user_stop:
            return True

    def get_model_time(self) -> float:
        return self._sim_time

    def set_initializer(
            self,
            fn: Initializer,
            args: Iterable[Any] = ()
    ) -> None:
        self._initializer = fn
        self._initializer_args = args

    def set_finalizer(self, fn: Finalizer) -> None:
        self._finalize = fn

    def set_context(self, context: object) -> None:
        self.context = context

    def get_curr_handler(self) -> object | None:
        """Получить последний вызванный обработчик или инициализатор."""
        return self.lhandler

    def set_max_sim_time(self, value: float) -> None:
        self._max_sim_time = value

    def set_max_real_time(self, value: float) -> None:
        self._max_real_time = value

    def set_max_num_events(self, value: int) -> None:
        self._max_num_events = value

    def future_events(self) -> list[tuple[EventId, float, Handler, tuple[Any]]]:
        """
        Получить список всех событий, которые сейчас находятся в очереди.
        Returns:
            list, в котором содержится приоритетная куча событий
        """
        return EventQueue.to_list()

    def build_runner(self, debug: bool = False) -> Iterator[ExecResult]:
        """
        Начинает выполнение модели.
        Извлекает события из очереди и вызывает их обработчики.
        Args:
            debug: bool режим работы модели. В случае True ... В случае False обычная работа ядра

        Returns:
            Описано в конце метода в yield
        """
        self._logger.setup()
        self._logger.debug("Старт симуляции")

        self.set_debug(debug)

        self._num_events_served = 0
        self._t_start = time.time()

        # 2) Создать экземпляр Simulator. Если контекст есть,
        #    использовать его. Если нет - использовать словарь (по-умолчанию)
        sim = Simulator(self, self.context)

        # 3) Инициализация модели
        self._initializer(sim, *self._initializer_args)

        if self._queue.empty:
            self.stop_reason = ExitReason.NO_MORE_EVENTS

        while not self._queue.empty and not self.stop_conditions():
            t, event_id, item = self._queue.pop()
            self._sim_time = t
            handler, args, msg = item
            handler(sim, *args)
            self._num_events_served += 1
            self.lhandler = handler
        if self._finalize:
            fin_ret = self._finalize(sim)

        yield (
            ExecutionStats(
                num_events_processed=self._num_events_served,
                sim_time=self._sim_time,
                time_elapsed=self.real_time_elapsed,
                exit_reason=self.stop_reason,
                stop_message=self.stop_msg,  # сообщение, если было
                last_handler=self.get_curr_handler(),
            ),
            sim.context,
            fin_ret,
        )

    @property
    def real_time_elapsed(self):
        return time.time() - self._t_start


def build_simulation(
        model_name: str,
        init: Initializer,
        init_args: Iterable[Any] = (),
        fin: Finalizer | None = None,
        context: object | None = None,
        max_real_time: float | None = None,
        max_sim_time: float | None = None,
        max_num_events: int | None = None,
        logger_config: ModelLoggerConfig | None = None,
        debug: bool = False,
) -> Iterator[ExecResult]:
    """
    Запустить симуляцию модели.
    Можно задать несколько условий остановки:

    - по реальному времени (сколько секунд до остановки)
    - по модельному времени
    - по числу событий

    Можно задать любое сочетания условий остановки, или ни одного. Модель
    остановится, когда любое из условий будет выполнено.

    Функцию инициализации надо передать обязательно, ее задача - запланировать
    первые события. Функцию завершения можно передавать или не передавать.
    Если передать функцию `fin`, то она будет вызвана после завершения
    симуляции, ее результат будет возвращен в третьем элементе
    кортежа-результата.

    Контекст можно передать явно, в виде словаря или объекта (например,
    некоторого dataclass-а). Если контекст не передать, то он будет
    инициализирован в пустой словарь. Контекст возвращается во втором
    элементе кортежа-результата.

    Args:
        model_name: название модели
        init: функция инициализации, обязательная
        init_args: кортеж аргументов функции инициализации
        fin: функция завершения, опциональная
        context: контекст (словарь или объект)
        max_real_time: реальное время, когда надо остановиться
        max_sim_time: модельное время, через которое надо остановиться
        max_num_events: сколько событий обработать до остановки
        logger_config: конфигурация логгера
        debug: если True, то запуститься в режиме отладки

    Returns:
        stats (ExecutionStats): статистика выполнения модели
        context (object): контекст модели
        fin_ret (object | None): результат вызова finalize(), если был вызов
    """
    # Создаем ядро
    kernel = Kernel(model_name)
    kernel.logger.setup(logger_config)

    # Настраиваем ядро
    kernel.set_initializer(init, init_args)
    if fin is not None:
        kernel.set_finalizer(fin)
    if max_real_time is not None:
        kernel.set_max_real_time(max_real_time)
    if max_sim_time is not None:
        kernel.set_max_sim_time(max_sim_time)
    if max_num_events is not None:
        kernel.set_max_num_events(max_num_events)

    # Создаем и передаем ядру контекст
    if context is not None:
        kernel.set_context(context)
    else:
        kernel.set_context(None)  # explicit is better than implicit (ZoP:2)

    kernel.set_debug(debug)

    # Запускаем модель и возвращаем все, что она вернет
    return kernel.build_runner()


def run_simulation(sim: Iterator[ExecResult]) -> ExecResult:
    ret = None
    try:
        while True:
            ret = next(sim)
            print('ret: ', ret)
    except StopIteration:
        pass
    if ret is None:
        raise RuntimeError("simulation yield no results")
    return ret
