import statistics
from pysim.sim import Simulator
from .objects import Model, Params, Result


def initialize(sim: Simulator, config: Params) -> None:
    """
    Первое событие, которое попадает в очередь событий.
    """
    model = Model(params=config, logger=sim.logger) # Задать контекст модели
    sim.context = model
    # Здесь запланировать первые события!!!
    sim.call(on_camera_detection)


def finalize(sim: Simulator) -> Result:
    """
    Последнее событие, исполняемое в симуляции.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context

    return Result(

    )


def on_camera_detection(sim: Simulator):
    """
    Обработчик события идентификации машины камерой.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context
    # Здесь должна быть логика из цикла while для события фото-транзита
    # Пример (зависит от исходной логики):
    # model.process_photo_transit()
    # После обработки, если нужно, запланировать следующее событие
    pass


def on_rfid_detection(sim: Simulator, num_id: int):
    """
    Обработчик события идентификации машины RFID считывателем.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context
    # Логика обработки события обнаружения RFID с номером num_id
    # Здесь должна быть логика из цикла while для события RFID detection
    # Пример (зависит от исходной логики):
    # model.process_rfid_detection(num_id)
    pass


def on_start_merge(sim: Simulator):
    """
    Обработчик события уточнения неполных данных с камеры данными
    от RFID системы.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context
    # Логика обработки события начала слияния
    # Здесь должна быть логика из цикла while для события начала слияния
    # Пример (зависит от исходной логики):
    # model.start_merge()
    pass

