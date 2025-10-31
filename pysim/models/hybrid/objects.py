from pydantic import BaseModel, Field, confloat, conint
from typing import List, Tuple, Optional

from pysim.sim.logger import ModelLogger


class Consts:
    MIN_MODEL_TYPE = 1
    MAX_MODEL_TYPE = 100


class Params(BaseModel):
    """
    Входные параметры модели
    """
    model_name: str = "Hybrid system"
    num_plates: conint(ge=1, le=50000) = Field(
        20000, description="Количество идентифицируемых автомобилей"
    )
    sign_prob: dict[str, float] = Field(
        default_factory=lambda: {
            "A": 0.1, "B": 0.1, "C": 0.1, "D": 0.1, "E": 0.1,
            "T": 0.1, "P": 0.1, "M": 0.1, "K": 0.1, "O": 0.1
        },
        description="Вероятности появления буквенных символов в"
                    "номерной табличке"
    )
    num_prob: dict[str, float] = Field(
        default_factory=lambda: {
            "0": 0.1, "1": 0.1, "2": 0.1, "3": 0.1, "4": 0.1,
            "5": 0.1, "6": 0.1, "7": 0.1, "8": 0.1, "9": 0.1
        },
        description="Вероятности появления цифр в номерной табличке"
    )
    speed_range: tuple[float, float] = Field(
        (60 / 3.6, 100 / 3.6),
        description="Разброс возможных скоростей машин, м/с"
    )
    transport_gap: float = Field(
        10, description="Расстояние между машинами"
    )
    photo_distance: tuple[float, float] = Field(
        (30, 50), description="Разброс возможных расстояний фотофиксации"
    )
    rfid_distance: tuple[float, float] = Field(
        (-5, 5),
        description="Разброс возможных расстояний идентификации RFID системой"
    )
    number_plate_symbols_amount: int = Field(
        6, description="Количество символов в номерной табличке"
    )
    photo_error: float = Field(
        0.7, description="Вероятность ошибки идентификации номерной таблички"
                         "с помощью камеры"
    )
    rfid_error: float = Field(
        0.1, description="Вероятность ошибки идентификации номерной таблички"
                         "RFID системой"
    )
    car_error: float = Field(
        0.3,
        description="Вероятность ошибки идентификации модели машины камерой"
    )
    @property
    def symbol_error(self) -> float:
        """
        Вероятность ошибки идентификации одного символа номерной таблички
        камерой
        """
        return 1 - (1 - self.photo_error) ** (
                1 / self.number_plate_symbols_amount
        )


class CarNumber(BaseModel):
    plate: str = Field(
        ..., description="Номерная табличка идентифицируемой машины"
    )
    car_model: Optional[int] = Field(
        ..., description="Идентификатор определённой модели машины."
    )


class CamDetection(BaseModel):
    """
    Объект, хранящий данные об одной идентифицированной
    номерной таблички машины
    """
    real_plate: str = Field(
        ..., description="Настоящая номерная табличка идентифицируемой машины"
    )
    photo_detection_time: float = Field(..., description="Время фотофиксации")
    photo_distance: float = Field(
        ..., description="Расстояние между камерой и машиной"
                         "в момент фотофиксации"
    )
    photo_num: str = Field(
        ..., description="Распознанная камерой информация с номера машины"
    )
    speed: float = Field(..., description="Скорость машины, м/с")
    real_car_model: int = Field(
        ..., description="Настоящая модель машины"
    )
    car_model: Optional[int] = Field(
        None, description="Идентификатор определённой модели машины."
                         "Если None, то не распознана"
    )


class RfidDetection(BaseModel):
    rfid_detection_time: float = Field(
        ..., description="Время идентификации RFID системой"
    )
    rfid_num: Optional[str] = Field(
        None, description="Идентифицированный номер RFID системой"
    )
    car_model: Optional[int] = Field(
        None, description="Идентификатор определённой модели машины."
    )


class Statistic(BaseModel):
    clear_cam_detections: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые были полностью"
                         "идентифицированы камерой"
    )
    error_cam_detections: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые не удалось распознать"
                         "камерой"
    )
    rfid_correction_without_collision: list[RfidDetection] = Field(
        ..., description="Список автомобилей, которые удалось распознать"
                         "RFID системой и которые не попали в коллизию"
    )
    error_rfid_detection: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые не удалось распознать ни"
                         "камерой, не RFID системой"
    )
    rfid_correction_after_collision: list[RfidDetection] = Field(
        ..., description="Список автомобилей, которые удалось распознать"
                         "RFID системой и которые попали в коллизию"
    )
    error_correction_after_collision: list[RfidDetection] = Field(
        ..., description="Список автомобилей, которые алгоритм разрешения"
                         "коллизий сопоставил неверно"
    )
    rfid_unresolved_collision: list[RfidDetection] = Field(
        ..., description="Список автомобилей, которые не удалось распознать"
                         "после попадания в коллизию"
    )


class Results(BaseModel):
    """Результаты симуляции"""
    cam_detect_prob: float = Field(
        ..., description="Вероятность идентификации машины только камерой"
    )
    rfid_detect_without_collision_prob: float = Field(
        ..., description="Вероятность уточнения неполных данных от камеры"
                         "RFID системой в случае без коллизий"
    )
    rfid_detect_with_collision_prob: float = Field(
        ..., description="Вероятность уточнения неполных данных от камеры"
                         "RFID системой в случае с коллизиями"
    )
    total_prob: float = Field(
        ..., description="Вероятность идентификации машины гибридной системой"
    )
    collision_amount_to_nums: float = Field(
        ..., description="Отношение количества номеров, попавших в коллизию"
                         "к суммарному количеству номеров"
    )
    error_collision_resolve_amount: float = Field(
        ..., description="Количество неправильно разрешённых коллизий"
    )
    unresolved_collision_amount: float = Field(
        ..., description="Количество неразрешённых коллизий"
    )


class Model:
    """
    Используется в качестве контекста модели.

    Содержит входные данные для симуляции и накапливает статистику в процессе
    работы программы.
    """
    def __init__(self, params: Params, logger: ModelLogger):
        self.params: Params = params
        self.statistics: Statistic = Statistic(
            clear_cam_detections = [],
            error_cam_detections = [],
            rfid_correction_without_collision = [],
            error_rfid_detection = [],
            rfid_correction_after_collision = [],
            error_correction_after_collision = [],
            rfid_unresolved_collision = []
        )
        self.current_detection: int = 0
        logger.debug("Модель успешно инициализирована")

