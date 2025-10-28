# from pysim.models.hybrid.objects import _CamDetections, _RfidDetections, CamDetection


def is_partial_match(photo_detections, rfid_detection):
    """
    Проверка на совпадение номерной таблички, частично распознанной камерой
    и полностью идентифицированной RFID системой.

    Пример работы:
    a228**          *4*7**          o148c*
    a228bc          e407to          a148co
    вернёт True     вернёт True     вернёт False

    """
    return [
        det for det in photo_detections
        if len(det.photo_num) == len(rfid_detection.rfid_num)
        and all(p == r or p == "*" for p, r in zip(det.photo_num, rfid_detection.rfid_num))
    ]


def compare_camera_and_rfid_detections(
    error_cam_detections,
    rfid_detection,
    sim,
):
    """
    Сравнение номерных табличек, полученных от камеры и RFID системы

    Args:
      - error_cam_detections: номера, распознанные камерой с ошибкой
      - rfid_detections: номера, распознанные RFID системой без ошибок
    """
    model = sim.context

    _time = (
            sum(model.params.photo_distance) + max(model.params.rfid_distance)
    ) / min(model.params.speed_range)
    corresponding_car_numbers = [
        number for number in error_cam_detections
        if number.photo_detection_time >= sim.time - _time
    ]
    # print("Времена идентификаций камерой")
    # for number in error_cam_detections:
    #     print(number.photo_detection_time)

    matching_numbers = []
    if len(corresponding_car_numbers) > 0:
        matching_numbers = is_partial_match(corresponding_car_numbers, rfid_detection)
    if len(matching_numbers) == 1:
        model.statistics.rfid_correction_without_collision.append(matching_numbers[0])

    # print(f"Номер RFID: {rfid_detection}")
    # print(f"Номера машин: {matching_numbers}")

    return None
