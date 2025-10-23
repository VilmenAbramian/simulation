from pysim.main import models_list
from pysim.models.hybrid.objects import _CamDetections, _RfidDetections, CamDetection
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


def compare_camera_and_rfid_detections(
    error_cam_detections: _CamDetections,
    rfid_detections: _RfidDetections,
    model,
) -> (list[CamDetection], list[CamDetection], list[CamDetection]):
    """
    Сравнение номерных табличек, полученных от камеры и RFID системы

    Args:
      - cam_detections: распознанные номера с помощью камеры
      - rfid_detections: распознанные номера с помощью RFID считывателя
    """
    corrected_by_rfid = []
    # failed_to_recognize = []

    for (rfid_detection, num_id) in rfid_detections:
        if rfid_detection.rfid_num is not None:

            _matched_detections = [
                _detection for _detection in error_cam_detections
                if is_partial_match(_detection[0].photo_num, rfid_detection.rfid_num)
            ]

            if len(_matched_detections) == 1:
                corrected_by_rfid.append(_matched_detections[0])
    model.results.corrected_by_rfid_detections.append(corrected_by_rfid)

            # elif len(_matched_transits) > 1:
            #     for transit in _matched_transits:
            #         if transit[0].car_model_detected:
            #             _match = find_match_num_id(num_id=num_id, transits=_matched_transits)
            #             corrected_by_rfid.append(_match)

    # for transit in error_cam_detections:
    #     if find_match_num_id(num_id=transit[1], transits=corrected_by_rfid) is None:
    #         failed_to_recognize.append(transit)

    return corrected_by_rfid
