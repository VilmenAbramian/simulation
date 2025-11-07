from pysim.models.hybrid.objects import CamDetection, RfidDetection
from pysim.sim.simulator import Simulator


def is_partial_match(
        photo_detections: list[CamDetection], rfid_detection: RfidDetection
) -> list[CamDetection]:
    """
    Возвращает список частично распознанных камерой номеров,
    которые соответствуют номеру, считанному RFID системой.

    Под "частичным распознаванием" понимается ситуация, когда
    отдельные символы номера камеры заменены на символ '*',
    обозначающий неопределённость. Совпадением считается такая
    пара (photo_num, rfid_num), где все известные символы совпадают,
    а символы '*' допускают любые значения.

    Пример:
        photo_num:  'A228**'
        rfid_num:   'A228BC'
        → Совпадает

        photo_num:  'A228**'
        rfid_num:   'B228BC'
        → Не совпадает

    Args:
        photo_detections (list[CamDetection]):
            Список объектов с данными идентификации от камеры,
            где поле `photo_num` может содержать неопределённые символы '*'.
        rfid_detection (RfidDetection):
            Результат считывания RFID, содержащий полный номерной знак.

    Returns:
        list[CamDetection]:
            Список объектов `CamDetection`, чьи номера частично совпадают
            с `rfid_num` по правилам сопоставления с символом '*'.

    """
    return [
        det for det in photo_detections
        if len(det.photo_num) == len(rfid_detection.rfid_num)
        and all(p == r or p == "*" for p, r in zip(
            det.photo_num, rfid_detection.rfid_num)
                )
    ]


def solve_collision(
        matching_numbers: list[CamDetection],
        rfid_detection: RfidDetection,
        sim: Simulator
) -> None:
    """
    Разрешение коллизии между несколькими кандидатами на один RFID номер.
    Под кандидатом здесь понимается один из неполностью распознанных номеров
    машины.

    Стратегия выбора:
    1) Сначала пытаемся найти того кандидата, модель которого совпадает с
        моделью из номера от RFID системы. Если таких кандидатов несколько, то:
    2) Предпочитаем кандидатов, у которых определена модель машины
        (cam.car_model не None);
    3) Среди них выбираем того, у которого наименьшее число неопределённых
        символов ('*');
    4) При равенстве выбираем того, у которого минимальная абсолютная разница
        по времени с RFID фиксацией.
    """
    if not matching_numbers:
        # Коллизия неразрешима, если список кандидатов пустой
        model = sim.context
        model.statistics.rfid_unresolved_collision.append(rfid_detection)
        return

    model = sim.context

    # 1. Сначала пытаемся найти уникальное совпадение по модели машины
    if rfid_detection.car_model is not None:
        model_matches = [m for m in matching_numbers if m.car_model == rfid_detection.car_model]
        if model_matches:
            matching_numbers = model_matches
        else:
            # Если все модели различаются — зафиксируем этот случай для статистики
            model.statistics.rfid_unresolved_collision.append(rfid_detection)
            # print(
            #     f"[!] Нет совпадений по модели для RFID {rfid_detection.rfid_num}, car_model={rfid_detection.car_model}")
            return
        if len(model_matches) == 1:
            model.statistics.rfid_correction_after_collision.append(model_matches[0])
            return
        elif len(model_matches) > 1:
            # Если несколько совпадений по модели, продолжаем разрешать по '*', времени
            matching_numbers = model_matches

    # Если у каких-то кандидатов есть распознанная модель, работаем только с ними
    candidates = [m for m in matching_numbers if getattr(m, "car_model", None) is not None]
    if not candidates:
        candidates = matching_numbers

    # Ключ сортировки: (число "*" в photo_num, абсолютная разница времени)
    def _score(det: CamDetection) -> tuple[int, float]:
        stars = det.photo_num.count("*")
        rfid_time = rfid_detection.rfid_detection_time or det.photo_detection_time
        time_diff = abs(det.photo_detection_time - rfid_time)
        return stars, time_diff

    best = min(candidates, key=_score)
    if best.real_plate != rfid_detection.rfid_num:
        model.statistics.error_correction_after_collision.append(best)
        # print(f"RFID номер: {rfid_detection}")
        # print(f"Номер от камеры: {best}")

    if best is None:
        model.statistics.rfid_unresolved_collision.append(rfid_detection)
        return

    model.statistics.rfid_correction_after_collision.append(best)
    return None


def compare_camera_and_rfid_detections(
    error_cam_detections: list[CamDetection],
    rfid_detection: RfidDetection,
    sim: Simulator,
) -> None:
    """
    Сравнение номерных табличек, полученных от камеры и RFID системы

    Args:
      - error_cam_detections: номера, распознанные камерой с ошибкой
      - rfid_detections: номера, распознанные RFID системой без ошибок
      - sim: объект ядра модели
    """
    model = sim.context

    max_travel_time = (
            sum(model.params.photo_distance) + max(model.params.rfid_distance)
    ) / min(model.params.speed_range)
    corresponding_car_numbers = [
        number for number in error_cam_detections
        if number.photo_detection_time >= sim.time - max_travel_time
    ]

    matching_numbers = []
    if len(corresponding_car_numbers) > 0:
        matching_numbers = is_partial_match(corresponding_car_numbers, rfid_detection)
    if len(matching_numbers) == 1:
        # Случай без коллизий
        model.statistics.rfid_correction_without_collision.append(matching_numbers[0])
    if len(matching_numbers) > 1:
        # Случай с коллизиями
        model.statistics.total_collisions += 1
        solve_collision(matching_numbers, rfid_detection, sim)

    # print(f"Номер RFID: {rfid_detection}")
    # print(f"Номера машин: {matching_numbers}")

    return None
