import numpy as np

from pysim.models.hybrid.objects import (
    CamDetection, CarNumber, Consts, RfidDetection
)
from pysim.models.hybrid.utils import check_probs


def generate_sign(probs: dict[str, float]) -> str:
    """
    Сгенерировать случайный символ для номерной таблички.

    Здесь реализован метод инверсии распределения. Для его работы
    probs должен быть нормализован (сумма вероятностей = 1).
    """
    generation = np.random.uniform()

    cur = 0
    for key in probs:
        cur += probs[key]

        if generation <= cur:
            return key


def generate_plate(
        sign_prob: dict[str, float], num_prob: dict[str, float]
) -> CarNumber:
    """
    Сгенерировать номерную табличку из случайных символов, взятых из словаря
    возможных символов.

    Внимание! Пока что не генерирует регион
    """
    check_probs(sign_prob)
    check_probs(num_prob)

    plate_sign = ""
    for _ in range(2): # Две случайные буквы
        plate_sign += generate_sign(sign_prob)

    plate_num = ""
    for _ in range(3): # Три случайные цифры
        plate_num += generate_sign(num_prob)

    return CarNumber(
        plate = plate_sign + plate_num + generate_sign(sign_prob),
        car_model = np.random.randint(Consts.MIN_MODEL_TYPE, Consts.MAX_MODEL_TYPE)
    )


def detect_car_by_camera(
        cur_time: float,
        sign_prob: dict[str, float],
        num_prob: dict[str, float],
        speed: tuple[float, float],
        distance: tuple[float, float],
        photo_error: float,
        car_error: float,
) -> CamDetection:
    """
    Распознавание номерной таблички с помощью камеры.

    Args:
      - cur_time: время вхождения машины в зону видимости камеры;
      - sign_prob: вероятность появления символа в номерной табличке;
      - num_prob: вероятность появления цифры в номерной табличке;
      - speed: минимальная и максимальная скорости, из которых выбирается
          случайное значение скорости для конкретной машины;
      - distance: минимальное и максимальное расстояния идентификации машины
          камерой;
      - photo_error: вероятность ошибки идентификации одного символа в номерной
          табличке;
      - car_error: вероятность ошибки идентификации модели машины (используется
          для разрешения коллизий).
    """
    car = generate_plate(sign_prob=sign_prob, num_prob=num_prob)
    number_plate = car.plate
    _speed = np.random.uniform(low=speed[0], high=speed[1]) # Случайная скорость конкретной машины
    _photo_distance = np.random.uniform(low=distance[0], high=distance[1])  # Случайное расстояние до конкретной машины
    num_val = []
    for value in list(number_plate):
        if np.random.uniform() <= photo_error:
            num_val.append("*")
        else:
            num_val.append(value)
    photo_number = "".join(num_val)

    if np.random.uniform() > car_error:
        car_model_detected = car.car_model
    else:
        car_model_detected = None

    return CamDetection(
        real_plate=number_plate,
        photo_detection_time=cur_time+_photo_distance/_speed,
        photo_distance=_photo_distance,
        photo_num=photo_number,
        speed=_speed,
        real_car_model=car.car_model,
        car_model=car_model_detected
    )


def detect_car_by_rfid(
        time: float,
        cam_detection: CamDetection,
        rfid_error: float,
) -> RfidDetection:
    if np.random.uniform() <= rfid_error:
        return RfidDetection(
            rfid_detection_time=time, rfid_num=None, car_model=None
        )
    return RfidDetection(
        rfid_detection_time=time,
        rfid_num=cam_detection.real_plate,
        car_model=cam_detection.real_car_model
    )
