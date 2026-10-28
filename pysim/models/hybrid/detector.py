import numpy as np
from typing import Tuple

from pysim.models.hybrid.objects import (
    CamDetection, CarNumber, Consts, Params, RfidDetection
)


SYMBOLS_AMOUNT = 8


def w_full_from_photo_error(photo_error: float) -> float:
    """Доля полностью нераспознанных номеров как функция от вероятности ошибки номера.

    Требования (приблизительно):
      photo_error=0.5 -> w_full≈0.8
      photo_error=0.25 -> w_full≈0.4
      photo_error=0.1 -> w_full≈0.1

    Используется гладкая S-образная зависимость вида:
      w = p^a / (p^a + c*(1-p)^a)
    где c=0.25 (чтобы w(0.5)=0.8), а a≈1.63093 (чтобы w(0.1)=0.1).
    """
    if not (0.0 <= photo_error <= 1.0):
        raise ValueError("photo_error must be in [0, 1]")

    if photo_error == 0.0:
        return 0.0
    if photo_error == 1.0:
        return 1.0

    a = 1.6309297535714575
    c = 0.25
    p = float(photo_error)
    pa = p ** a
    qa = (1.0 - p) ** a
    return pa / (pa + c * qa)


def weights_from_photo_error(
    photo_error: float,
    ratio_2: float = 1.0,
    ratio_3: float = 1.0,
) -> tuple[float, float, float]:
    """Возвращает (w_full, w_3, w_2) как функции от photo_error.

    Оставшуюся после w_full массу распределяем между случаями "2 звезды" и "3 звезды"
    в фиксированной пропорции ratio_3:ratio_2.
    """
    w_full = w_full_from_photo_error(photo_error)
    rest = max(0.0, 1.0 - w_full)

    s = ratio_2 + ratio_3
    if s <= 0:
        raise ValueError("ratio_2 and ratio_3 must sum to positive")

    w_2 = rest * (ratio_2 / s)
    w_3 = rest * (ratio_3 / s)
    return w_full, w_3, w_2

def make_miss_count_dist(
    photo_error: float,
    w_full: float = None,
    w_3: float = None,
    w_2: float = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Пересчёт долей нераспозннаных символов в номере в:
    values: количество нераспознанных символов в номере k. k ∈ {0, 2, 3, 8}
      т.е. при k = 0 распознаны все символы в номере, а при k = 8 не распознан
      ни один символ в номере.
    probs: вероятность того, что в номере не будет распознано ровно k символов.
      Сумма probs ОБЯЗАТЕЛЬНО должна быть равна 1. Только в этом случае будут
      покрыты все возможные случаи нераспознавания того или иного количества
      симвлов в номере.

    Args:
        photo_error: вероятность, что хотя бы один символ в номере не распознан
        w_full: доля полностью не распознанных номеров
        w_3: доля "не распознано 3 символа"
        w_2: доля "не распознано 2 символа"
    """
    if not (0.0 <= photo_error <= 1.0):
        raise ValueError("photo_error must be in [0, 1]")

    s = w_full + w_3 + w_2
    if s <= 0:
        raise ValueError("weights must sum to positive")

    # нормируем на всякий случай
    w_full, w_3, w_2 = w_full / s, w_3 / s, w_2 / s

    values = np.array([0, 2, 3, SYMBOLS_AMOUNT], dtype=int)
    probs = np.array([
        1.0 - photo_error,
        photo_error * w_2,
        photo_error * w_3,
        photo_error * w_full,
    ], dtype=float)

    # микрокоррекция на float-ошибки
    probs[-1] += 1.0 - probs.sum()
    return values, probs


def recognize_plate_camera(
    number_plate: str,
    photo_error: float,
    rng: np.random.Generator | None = None,
    w_full: float = 0.33,
    w_3: float = 0.0,
    w_2: float = 0.67,
    mask_char: str = "*",
) -> str:
    """
    Посимвольное распознавание номера камерой.
    Args:
        number_plate: автомобильный номер - строка длины 8
        photo_error: вероятность ошибки РАСПОЗНАВАНИЯ ВСЕГО НОМЕРА (0..1)
        rng:
        w_full: доля полностью не распознанных номеров (если None, вычисляется автоматически по photo_error)
        w_3: доля "не распознано 3 символа" (если None, вычисляется автоматически по photo_error)
        w_2: доля "не распознано 2 символа" (если None, вычисляется автоматически по photo_error)
        mask_char: заменитель для нераспознанного символа в номере
    """
    if len(number_plate) != SYMBOLS_AMOUNT:
        raise ValueError(f"number_plate must have length {SYMBOLS_AMOUNT}")

    rng = rng or np.random.default_rng()

    values, probs = make_miss_count_dist(photo_error, w_full=w_full, w_3=w_3, w_2=w_2)
    k = int(rng.choice(values, p=probs))  # сколько символов замаскировать

    if k == 0:
        return number_plate

    # выбираем k позиций под звёздочки
    idx = rng.choice(SYMBOLS_AMOUNT, size=k, replace=False)
    chars = list(number_plate)
    for i in idx:
        chars[i] = mask_char
    return "".join(chars)


def check_probs(probs: dict[str, float]):
    """Валидация величин вероятности"""
    for value in probs.values():
        assert 0 <= value <= 1

    assert abs(sum(probs.values()) - 1) < 1e-6


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
    """
    check_probs(sign_prob)
    check_probs(num_prob)

    plate_sign = ""
    for _ in range(2):  # Две случайные буквы
        plate_sign += generate_sign(sign_prob)

    plate_num = ""
    for _ in range(3):  # Три случайные цифры
        plate_num += generate_sign(num_prob)

    region_num = ""
    for _ in range(2):  # Две случайные цифры региона
        region_num += generate_sign(num_prob)

    return CarNumber(
        plate=plate_sign + plate_num + generate_sign(sign_prob) + region_num,
        car_model=np.random.randint(
            Consts.MIN_MODEL_TYPE, Consts.MAX_MODEL_TYPE
        )
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
    print(f"Автомобильный номер: {car.plate}")
    number_plate = car.plate
    # Случайная скорость конкретной машины
    _speed = np.random.uniform(low=speed[0], high=speed[1])
    # Случайное расстояние до конкретной машины
    _photo_distance = np.random.uniform(low=distance[0], high=distance[1])
    # num_val = []
    # for value in list(number_plate):
    #     if np.random.uniform() <= photo_error:
    #         num_val.append("*")
    #     else:
    #         num_val.append(value)
    # photo_number = "".join(num_val)

    full_number_error = 1 - (1 - photo_error) ** SYMBOLS_AMOUNT
    photo_number = recognize_plate_camera(number_plate, full_number_error)

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
