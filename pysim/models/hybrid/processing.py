from pysim.models.hybrid.objects import Results, Statistic, Params


def formalize_results(
        params: dict,
        model_statistics: Statistic,
        print_res: bool = False
) -> Results:
    cam_prob = (len(model_statistics.clear_cam_detections) /
                params["num_plates"])
    rfid_without_collision_prob = len(
            model_statistics.rfid_correction_without_collision
        ) / params["num_plates"]
    rfid_with_collision_prob = len(
            model_statistics.rfid_correction_after_collision
        ) / params["num_plates"]
    resolve_collisions = len(model_statistics.error_correction_after_collision)
    unresolved_collisions = len(model_statistics.rfid_unresolved_collision)

    results = Results(
        cam_detect_prob = cam_prob,
        rfid_detect_without_collision_prob = rfid_without_collision_prob,
        rfid_detect_with_collision_prob = rfid_with_collision_prob,
        total_prob = cam_prob + rfid_without_collision_prob + rfid_with_collision_prob,
        collision_amount_to_nums = (resolve_collisions + unresolved_collisions)
                                   / params["num_plates"],
        error_collision_resolve_amount = resolve_collisions,
        unresolved_collision_amount = unresolved_collisions
    )
    if print_res:
        print_results(params, results)

    return results


def print_results(params:dict, results: Results) -> None:
    print("\n📊 Результаты моделирования")
    print("-" * 60)
    print(f"{'Ошибка камеры':35} {1 - (1 - params['photo_error']) ** Params().number_plate_symbols_amount:<.3f}")
    print(f"{'Ошибка RFID':35} {params['rfid_error']}")
    print(f"{'Ошибка модели автомобиля':35} {params['car_error']:<.3f}")
    print("-" * 60)
    print(f"{'Идентификация камерой':35} {results.cam_detect_prob:<.3f}")
    print(f"{'Уточнение без коллизий (RFID)':35} {results.rfid_detect_without_collision_prob:<.3f}")
    print(f"{'Уточнение с коллизиями (RFID)':35} {results.rfid_detect_with_collision_prob:<.3f}")
    print(f"{'Суммарная вероятность':35} {results.total_prob:<.3f}")
    print("-" * 60)
    print(f"{'Частота коллизий':35} {results.collision_amount_to_nums:<.3f}")
    print(f"{'Неправильно разрешённые':35} {results.error_collision_resolve_amount}")
    print(f"{'Неразрешённые коллизии':35} {results.unresolved_collision_amount}")
    print("-" * 60)


