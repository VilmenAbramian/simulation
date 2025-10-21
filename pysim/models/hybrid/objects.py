from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Tuple, Optional

from pysim.sim.logger import ModelLogger

# Вероятность появления буквенного символа в номерной табличке
sign_prob = {
    "A": 0.1,
    "B": 0.1,
    "C": 0.1,
    "D": 0.1,
    "E": 0.1,
    "T": 0.1,
    "P": 0.1,
    "M": 0.1,
    "K": 0.1,
    "O": 0.1
}

# Вероятность появления цифры в номерной табличке
num_prob = {
    "0": 0.1,
    "1": 0.1,
    "2": 0.1,
    "3": 0.1,
    "4": 0.1,
    "5": 0.1,
    "6": 0.1,
    "7": 0.1,
    "8": 0.1,
    "9": 0.1
}


class Params(BaseModel):
    """
    Входные параметры модели
    """
    sign_prob: dict[str, float] = Field(
        ..., description="Вероятности появления буквенных символов"
    )
    num_prob: dict[str, float] = Field(
        ..., description="Вероятности появления цифр"
    )
    average_speed: float = Field(..., description="Средняя скорость, м/с")
    transport_distance: float = Field(
        ..., description="Расстояние между машинами"
    )
    photo_distance: float = Field(..., description="Расстояние фотофиксации")
    rfid_distance: float = Field(
        ..., description="Расстояние идентификации RFID системой"
    )
    photo_error: float = Field(
        ..., description="Вероятность ошибочного определения"
                         "одного символа номерной таблички"
    )
    rfid_error: float = Field(
        ..., description="Вероятность идентификации номерной таблички"
                         "RFID системой"
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
    car_model_detected: bool = Field(
        ..., description="Обнаружена ли модель машины"
    )


class RfidDetection(BaseModel):
    rfid_detection_time: float = Field(
        ..., description="Время идентификации RFID системой"
    )
    rfid_num: Optional[float] = Field(
        None, description="Идентифицированный номер RFID системой"
    )


class Result(BaseModel):
    clear_cam_detections: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые были полностью"
                         "идентифицированы камерой"
    )
    corrected_by_rfid_detections: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые не удалось распознать"
                         "камерой, но которые получилось уточнить с помощью"
                         "RFID системы"
    )
    failed_to_recognize: list[CamDetection] = Field(
        ..., description="Список автомобилей, которые не удалось распознать"
    )


class Model:
    """
    Используется в качестве контекста модели.

    Содержит входные данные для симуляции и накапливает статистику в процессе
    работы программы.
    """
    def __init__(self, params: Params, logger: ModelLogger):
        self.params = params
        self.results = Result(
            clear_cam_detections=[],
            corrected_by_rfid_detections=[],
            failed_to_recognize=[]
        )

        logger.debug("Модель успешно инициализирована")


class _Event(Enum):
    PHOTO_TRANSIT = 0
    RFID_DETECTION = 1
    START_MERGE = 2


_EventQueue = List[Tuple[float, _Event, Optional[int]]]
_Transits = List[Tuple[CamDetection, int]]
_RfidDetections = List[Tuple[RfidDetection, int]]