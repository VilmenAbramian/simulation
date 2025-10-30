import json
from tabulate import tabulate
import time


def save_results_to_file(initial_data, res):
    current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    filename = "results/" + "model_res-" + current_time + ".txt"
    with open(filename, "w") as f:
        f.write("Входные параметры: " + json.dumps(initial_data) + "\n")
        f.write("Результаты моделирования: " + json.dumps(res))


def print_results_to_terminal(initial_data, res, many_results):
    if many_results:
        var_arg_names = ("interval", "channel_delay", "service_delay",
                         "loss_prob", "max_pings")
        print("Результаты серии численных экспериментов")
        print("\nТаблица параметров:\n")
        print(tabulate([(name, initial_data[name]) for name in var_arg_names],
                       tablefmt="pretty"))

        print("\nТаблица результатов:\n")
        res_arg_names = ("avg_interval", "avg_delay", "miss_rate")
        print(
            tabulate(
                [(name, res[name]) for name in res_arg_names],
                tablefmt="pretty"
            )
        )
    else:
        print("Результаты одиночного моделирования:\n"
              f"Параметры: {initial_data}\n"
              "- Средний интервал отправки Ping клиентом"
              f"(условные единицы) = {res['avg_interval']}\n",
              "- Средняя длительность передачи сообщения"
              f"(условные единицы) = {res['avg_delay']}\n",
              f"- Вероятность потери сообщения = {res['miss_rate']}", sep=""
              )


def result_processing(initial_data, results, variadic, save_results=False):
    """
    Обработка полученных данных из модели.

    Если save_results = True, то входные и
    выходные данные сохраняются в .txt файл в
    папке results.

    Далее данные выводятся в терминал
    """
    # Преобразуем данные из типа Result (pydentic) в dict
    res = {
        "avg_interval": [],
        "avg_delay": [],
        "miss_rate": []
        }
    if isinstance(results, list):
        for i in range(len(results)):
            res["avg_interval"].append(results[i].avg_interval),
            res["avg_delay"].append(results[i].avg_delay),
            res["miss_rate"].append(results[i].miss_rate)
    else:
        res = results.dict()

    # Запись данных в файл
    if save_results:
        save_results_to_file(initial_data, res)

    # Вывод данных в терминал
    print_results_to_terminal(
        initial_data, res, isinstance(results, list)
    )
