from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional


@dataclass
class ModelParams:
    """
    Входные параметры
    """
    sign_prob: dict[str, float]
    num_prob: dict[str, float]
    average_speed: float
    transport_distance: float
    photo_distance: float
    rfid_distance: float
    photo_error: float
    rfid_error: float


@dataclass
class Transit:
    num: str
    photo_detection_time: float
    photo_distance: float
    photo_num: str
    speed: float
    car_model_detected: bool


@dataclass
class RfidDetection:
    rfid_detection_time: float
    rfid_num: Optional[float]


class ModelResults:
    unmatched_transits: list[Transit]
    matched_transits: list[Transit]

    def __init__(self):
        self.unmatched_transits = []
        self.matched_transits = []


class _Event(Enum):
    PHOTO_TRANSIT = 0
    RFID_DETECTION = 1
    START_MERGE = 2


_EventQueue = List[Tuple[float, _Event, Optional[int]]]
_Transits = List[Tuple[Transit, int]]
_RfidDetections = List[Tuple[RfidDetection, int]]