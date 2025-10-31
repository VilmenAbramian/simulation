import numpy as np
from pprint import pprint

from pysim.sim import Simulator
from pysim.models.hybrid.comparator import compare_camera_and_rfid_detections
from pysim.models.hybrid.detector import detect_car_by_camera, detect_car_by_rfid
from pysim.models.hybrid.objects import CamDetection, Model, Params, Statistic


def initialize(sim: Simulator, config: Params) -> None:
    """
    Первое событие, которое попадает в очередь событий.
    """
    model = Model(params=config, logger=sim.logger) # Задать контекст симуляции
    sim.context = model
    sim.call(on_camera_detection, (sim,))


def finalize(sim: Simulator) -> Statistic:
    """
    Последнее событие, исполняемое в симуляции.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context

    return model.statistics


def on_camera_detection(sim: Simulator, _) -> None:
    """
    Обработчик события идентификации машины камерой.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context
    cam_detection = detect_car_by_camera(
        cur_time = sim.time,
        sign_prob=model.params.sign_prob,
        num_prob=model.params.num_prob,
        speed=model.params.speed_range,
        distance=model.params.photo_distance,
        photo_error=model.params.photo_error,
        car_error=model.params.car_error,
    )
    if "*" not in cam_detection.photo_num:
        model.statistics.clear_cam_detections.append(cam_detection)
    else:
        model.statistics.error_cam_detections.append(cam_detection)
        # Идентифицируем эту же машину RFID системой
        sim.schedule(
            _get_rfid_detection_time(
                speed = cam_detection.speed,
                photo_distance = cam_detection.photo_distance,
                rfid_distance = model.params.rfid_distance,
            ),
            on_rfid_detection,
            (cam_detection,)
        )
    model.current_detection += 1

    # Фотоидентифицируем следующую машину
    if model.current_detection < model.params.num_plates:
        sim.schedule(
            _get_photo_time(
                speed = cam_detection.speed,
                distance_between_transports = model.params.transport_gap,
            ),
            on_camera_detection,
            (sim,)
        )


def on_rfid_detection(sim: Simulator, cam_detection: CamDetection) -> None:
    """
    Обработчик события идентификации машины RFID считывателем.
    Запускается только в случае неуспешной фотофиксации.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context

    rfid_detection = detect_car_by_rfid(
        time=sim.time,
        cam_detection=cam_detection,
        rfid_error=model.params.rfid_error,
    )
    if rfid_detection.rfid_num is not None:
        sim.call(on_start_merge, (rfid_detection,))
    else:
        model.statistics.error_rfid_detection.append(cam_detection)


def on_start_merge(sim: Simulator, rfid_detection) -> None:
    """
    Обработчик события уточнения неполных данных с камеры данными
    от RFID системы.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context

    compare_camera_and_rfid_detections(
        model.statistics.error_cam_detections,
        rfid_detection,
        sim
    )


def _get_photo_time(
        speed: float,
        distance_between_transports: float
) -> float:
    """
    Расчёт времени в секундах до вхождения следующей машины в зону видимости
    камеры
    """
    time = distance_between_transports / speed
    return time


def _get_rfid_detection_time(
        speed: float,
        photo_distance: float,
        rfid_distance: [float, float],
) -> float:
    """
    Расчёт времени в секундах до начала RFID идентификации.

    Args:
        speed: скорость идентифицируемой машины
        photo_distance: расстояние между камерой и идентифицированной ей
          машиной
        rfid_distance: диапазон расстояния, на котором машина может быть
          идентифицирована RFID системой
    """
    return (photo_distance - np.random.uniform(
        low=rfid_distance[0], high=rfid_distance[1]
    )) / speed

