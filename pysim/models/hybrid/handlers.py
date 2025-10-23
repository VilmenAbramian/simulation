import numpy as np

from pysim.sim import Simulator
from pysim.models.hybrid.detector import detect_car_by_camera, detect_car_by_rfid
from pysim.models.hybrid.objects import Model, Params, Result


def initialize(sim: Simulator, config: Params) -> None:
    """
    Первое событие, которое попадает в очередь событий.
    """
    model = Model(params=config, logger=sim.logger) # Задать контекст модели
    sim.context = model
    sim.call(on_camera_detection, (sim,))
    # sim.call(on_start_merge, (sim,))


def finalize(sim: Simulator) -> Result:
    """
    Последнее событие, исполняемое в симуляции.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context

    return model.results


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
    model.cam_detections.append((cam_detection, model.current_detection))
    if "*" not in cam_detection.photo_num:
        model.results.clear_cam_detections.append(cam_detection)
    else:
        model.error_cam_detections.append((cam_detection, model.current_detection))

    # Идентифицируем эту же машину RFID системой
    # sim.schedule(
    #     _get_rfid_detection_time(
    #         cur_time = sim.time,
    #         speed = cam_detection.speed,
    #         photo_distance = cam_detection.photo_distance,
    #         rfid_distance = model.params.rfid_distance,
    #     ),
    #     on_rfid_detection,
    #     (sim, model.current_detection)
    # )
    model.current_detection += 1
    # Фотоидентифицируем следующую машину
    if model.current_detection <= model.params.num_plates:
        sim.schedule(
            _get_photo_time(
                cur_time = sim.time,
                speed = cam_detection.speed,
                distance_between_transports = model.params.transport_distance,
            ),
            on_camera_detection,
            (sim,)
        )


def on_rfid_detection(sim: Simulator, current_detection_id: int) -> None:
    """
    Обработчик события идентификации машины RFID считывателем.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context
    matches = [_cam_detection for _cam_detection in model.cam_detections if _cam_detection[1] == current_detection_id]

    if len(matches) == 0:
        raise Exception(f"Некорректный id номерной таблички: {current_detection_id}")

    rfid_detection = detect_car_by_rfid(
        time=sim.time,
        cam_detection=matches[0][0],
        rfid_error=model.params.rfid_error,
    )

    model.rfid_detections.append((rfid_detection, current_detection_id))


def on_start_merge(sim: Simulator, _) -> None:
    """
    Обработчик события уточнения неполных данных с камеры данными
    от RFID системы.
    """
    assert isinstance(sim.context, Model)
    model: Model = sim.context


def _get_photo_time(
        cur_time: float,
        speed: float,
        distance_between_transports: float
) -> float:
    """
    Расчёт времени в секундах до начала следующей фотофиксации
    """
    return cur_time + distance_between_transports / speed


def _get_rfid_detection_time(
        cur_time: float,
        speed: float,
        photo_distance: float,
        rfid_distance: [float, float],
) -> float:
    """
    Расчёт времени в секундах до начала следующей RFID идентификации
    """
    return cur_time + (photo_distance - np.random.uniform(
        low=rfid_distance[0], high=rfid_distance[1]
    )) / speed

