from pysim.models.hybrid.objects import CamDetection, RfidDetection
from pysim.models.hybrid.utils import check_probs


def is_partial_match(photo_num: str, rfid_num: str) -> bool:
    """
    Проверка на совпадение номерной таблички, частично распознанной камерой
    и полностью идентифицированной RFID системой.

    Пример работы:
    a228**          *4*7**          o148c*
    a228bc          e407to          a148co
    вернёт True     вернёт True     вернёт False

    """
    if len(photo_num) != len(rfid_num):
        return False
    return all(p == r or p == "*" for p, r in zip(photo_num, rfid_num))


def compare_transits_and_rfid_detections(
    error_cam_detections: _Transits,
    rfid_detections: _RfidDetections
) -> (list[Transit], list[Transit], list[Transit]):
    """
    Реализация алгоритма сравнения распознанных номерных табличек с помощью
    камеры и с помощью RFID считывателя.

    Args:
      - cam_detections: распознанные номера с помощью камеры
      - rfid_detections: распознанные номера с помощью RFID считывателя
    """
    corrected_by_rfid: list[_Transits] = []
    failed_to_recognize: list[_Transits] = []

    for (detection, num_id) in rfid_detections:
        if detection.rfid_num is not None:

            _matched_transits = [
                _transit for _transit in error_cam_detections
                if is_partial_match(_transit[0].photo_num, detection.rfid_num)
            ]

            if len(_matched_transits) == 1:
                corrected_by_rfid.append(_matched_transits[0])

            elif len(_matched_transits) > 1:
                for transit in _matched_transits:
                    if transit[0].car_model_detected:
                        _match = find_match_num_id(num_id=num_id, transits=_matched_transits)
                        corrected_by_rfid.append(_match)

    for transit in error_cam_detections:
        if find_match_num_id(num_id=transit[1], transits=corrected_by_rfid) is None:
            failed_to_recognize.append(transit)

    return corrected_by_rfid, failed_to_recognize
