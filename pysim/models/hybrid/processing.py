from typing import List, Union
from tabulate import tabulate

from pysim.models.hybrid.objects import Results, Statistic, Params


def formalize_results(
        params: dict,
        model_statistics: Statistic
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
        cam_detect_prob=cam_prob,
        rfid_detect_without_collision_prob=rfid_without_collision_prob,
        rfid_detect_with_collision_prob=rfid_with_collision_prob,
        total_prob=cam_prob + rfid_without_collision_prob + rfid_with_collision_prob,
        collision_amount_to_nums=(resolve_collisions + unresolved_collisions)
                                 / params["num_plates"],
        error_collision_resolve_amount=resolve_collisions,
        unresolved_collision_amount=unresolved_collisions
    )

    return results


def print_mult_results_to_terminal(initial_data: dict, results: list[Results], variadic: str):
    """
    Выводит таблицу параметров и результатов для серии симуляций с изменяющимся параметром.
    """
    params_names = ["photo_error", "rfid_error", "car_error", "speed", "transport_gap"]
    params_names.remove(variadic)

    print("\n# СТАТИЧЕСКИЕ ПАРАМЕТРЫ:\n")
    print(tabulate([(name, initial_data[name]) for name in params_names],
                   tablefmt="pretty"))

    ret_cols = [
        "cam_detect_prob",
        "rfid_detect_without_collision_prob",
        "rfid_detect_with_collision_prob",
        "total_prob",
        "collision_amount_to_nums",
        "error_collision_resolve_amount",
        "unresolved_collision_amount"
    ]
    readable_headers = [
        "Идентификация камерой",
        "RFID без коллизий",
        "RFID с коллизиями",
        "Суммарная вероятность",
        "Доля коллизий",
        "Ошибки при разрешении",
        "Неразрешённые коллизии"
    ]

    results_table = [
        [round(getattr(item, col), 3) if isinstance(getattr(item, col), float) else getattr(item, col)
         for col in ret_cols]
        for item in results
    ]

    ret_cols.insert(0, variadic)
    for i, value in enumerate(initial_data[variadic]):
        results_table[i].insert(0, value)

    print("\n# РЕЗУЛЬТАТЫ:\n")
    print(tabulate(results_table, headers=readable_headers, tablefmt="pretty"))


def result_processing(
        params: Union[dict, list[dict]],
        model_statistics: Union[Statistic, list[Statistic]],
        variadic: Union[str, None],
        print_res: bool = False
) -> Union[Results, list[Results]]:
    if variadic is None:
        results = formalize_results(params, model_statistics)
        if print_res:
            print_single_results(params, results)
        return results
    else:
        results = [
            formalize_results(params, stat)
            for stat in model_statistics
        ]
        if print_res:
            print_mult_results_to_terminal(params, results, variadic)
        return results


def print_single_results(params:dict, results: Results) -> None:
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
