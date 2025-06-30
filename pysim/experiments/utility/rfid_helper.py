# ##################################################
# Функции для запуска моделирования и построения графиков для
# группы сетов имитационных моделей RFID систем.
#
# Используется в блокнотах:
# 1) rfid_single_tag.ipynb
# 2) rfid_multiple_tag.ipynb
# ##################################################
import json
import os

from matplotlib.ticker import MaxNLocator
from tqdm import tqdm
from typing import Callable, Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np

from pysim.experiments.utility.graphs_style import savefig, setup_matplotlib
from pysim.models.rfid.cli import prepare_multiple_simulation
from pysim.models.rfid.params import (
    default_params, multipliers, inner_params
)
from pysim.experiments.utility.channel_helper import(
    find_zones, get_tag_rx
)

setup_matplotlib()


IMAGE_DIRECTORY = "rfid/"
JSON_DIRECTORY = "../results/result_jsons/rfid/"
SAVE_FIG = False         # Сохранять ли изображения
SAVE_RESULTS = False     # Сохранять ли результаты в JSON
USE_JSON = True          # Использовать ли результаты из JSON


def convert_non_serializable(obj: Any) -> Any:
    """
    Преобразует не сериализуемые объекты (например, функции) в строки
    для последующего сохранения в JSON.
    """
    return str(obj)


def calculate_simulations(
    variable: str,
    variable_values: list,
    params_list: list[dict],
    key_fn: Callable[[dict], str],
    use_json: bool = USE_JSON,
    save_results: bool = SAVE_RESULTS,
    json_directory: str = JSON_DIRECTORY,
    file_name: str = "probs",
) -> dict[str, dict[str, list[Any]]]:
    """
    Запуск нескольких сетов моделирования и получение зависимостей
    вероятности чтения от варьируемого параметра.

    Args:
        variable: имя переменной, в зависимости от которой
          исследуется вероятность;
        variable_values: список значений переменной variable (ось абсцисс);
        params_list: список параметров для разных кривых каждого
          сета моделирования;
        key_fn: функция, формирующая имя кривой по параметрам из params_list;
        use_json: если True, то попытаться загрузить результаты из JSON;
        save_results: если True, сохранить результаты в JSON;
        json_directory: директория сохранения результатов в JSON;
        file_name: имя файла JSON.

    Returns:
        read_user_probs: словарь, где ключ — имя кривой,
          значение — список вероятностей.
    Raises:
        ValueError в случае попытки чтения несуществующих результатов из
          json-файла
    """
    directory = json_directory + file_name
    results = {}  # Сбор всех результатов моделирования
    rounds_count = {}
    inventory_probs = {}
    read_user_probs = {}
    times_count = {}
    collision_counts = {} # Среднее количество коллизий
    execution_times = {}
    if use_json and os.path.exists(directory):
        with open(directory, "r") as f:
            data = json.load(f)
            if "Results" not in data:
                raise ValueError(
                    f"Файл {directory} не содержит блока 'Results'"
                )
            results = data["Results"]
    else:
        for params in tqdm(
                params_list, desc=f"Моделирование по переменной {variable}"
        ):
            sim_results = prepare_multiple_simulation(
                variable, **{variable: variable_values}, **params
            )
            key = key_fn(params)
            rounds_count[key] = [res.rounds_per_tag for res in sim_results]
            inventory_probs[key] = [res.inventory_prob for res in sim_results]
            read_user_probs[key] = [res.read_tid_prob for res in sim_results]
            times_count[key] = [res.read_tid_time for res in sim_results]
            collision_counts[key] = [res.avg_collisions for res in sim_results]
            execution_times[key] = [res.execution_time for res in sim_results]

        results["rounds_count"] = rounds_count
        results["inventory_probs"] = inventory_probs
        results["read_user_probs"] = read_user_probs
        results["times_count"] = times_count
        results["collision_counts"] = collision_counts
        results["execution_times"] = execution_times

        if save_results:
            os.makedirs(os.path.dirname(directory), exist_ok=True)
            with open(directory, "w") as f:
                json.dump({
                    "Input parameters list": params_list,
                    "Results": results
                }, f, indent=2, default=convert_non_serializable)
    return results


def plot_simulations_results(
    results_list: list[dict[str, list[float]]],
    labels_list: list[str] | list[list[str]],
    titles: list[str],
    x_variable: list[float],
    x_label: str,
    y_label: str = "Вероятность чтения\nбанка памяти USER",
    unified_legend: bool = False,
    image_name: str = "Probs",
    save_fig: bool = SAVE_FIG,
    image_directory: str = IMAGE_DIRECTORY,
    integer_labels: bool = False,
) -> None:
    """
    Построение графиков зависимости вероятности чтения
    от произвольного параметра для нескольких сетов моделирования.

    Args:
        results_list: список словарей с результатами;
        labels_list: ключи и подписи для легенд;
        titles: заголовки для подграфиков;
        x_variable: значения variable для оси OX;
        x_label: подпись оси X;
        y_label: подпись оси Y;
        unified_legend: использовать ли одну легенду для обоих графиков
        image_name: имя файла;
        save_fig: сохранять ли картинку;
        image_directory: директория сохранения картинки;
        integer_labels: использовать целые числа по оси абсцисс.
    """
    graphs_amount = len(results_list) # Количество графиков
    fig, axes = plt.subplots(figsize=(7 * graphs_amount, 5), ncols=graphs_amount)

    if graphs_amount == 1:
        axes = [axes]
        labels_list = [labels_list]

    graph_num = 0 # В случае использования общей легенды для 2х изображений нужно считать построенные графики
    for ax, results, labels, title in zip(
        axes, results_list, labels_list, titles
    ):
        for key in labels:
            y_vals = results[key]
            ax.plot(x_variable, y_vals, label=key, marker='o')
        ax.set_title(title)
        ax.set_xlabel(x_label)
        if integer_labels:
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel(y_label)
        ax.grid()
        if not (unified_legend and graph_num >= 1):
            legend_pos = 0.5
            if unified_legend:
                legend_pos = 1
            ax.legend(
                loc="upper center",
                bbox_to_anchor=(legend_pos, -0.15),
                ncol=2,
            )
        graph_num += 1

    if save_fig:
        savefig(name=image_name, directory=image_directory)


def estimate_generation_interval(
    tags_amount: int,
    reading_zone: float,
    speed: float = default_params.speed
) -> float:
    """
    Пересчитывает желаемое количество меток в зоне чтения в требуемый интервал генерации.

    На количество меток в зоне чтения влияет размер зоны чтения (зависит от канала),
    скорость движения и период генерации меток.

    Args:
        tags_amount: желаемое количество меток в зоне
        reading_zone: суммарная длина зон, где метка включена (в метрах)
        speed: скорость движения считывателя, км/ч

    Returns:
        Интервал генерации в секундах (временной промежуток между метками)
    """
    return reading_zone / (tags_amount * speed * multipliers.KMPH_TO_MPS)


def compute_reading_zone(
        speed: float = default_params.speed,
        power_dbm: float = default_params.power_dbm,
) -> float:
    """
    Вычисляет суммарную длину зоны активности меток, то есть суммарную длину отрезков,
    на которых принимаемая мощность сигнала от считывателя на метке превышает порог.

    Args:
        speed: скорость считывателя, км/ч
        power_dbm: мощность передатчика считывателя, дБм

    Returns:
        Суммарная длина зон активации (в метрах)
    """
    ox_axis = np.linspace(
        - inner_params.geometry_params.initial_distance_to_reader, # Начальная точка движения
        inner_params.geometry_params.initial_distance_to_reader, # Конечная точка движения
        inner_params.geometry_params.grid_step
    )
    tag_accepted_power = [get_tag_rx(x, speed=speed, t=0, power=power_dbm) for x in ox_axis]
    tag_on_intervals = find_zones(ox_axis, tag_accepted_power, use_upper=True)
    return sum(end - start for start, end in tag_on_intervals)


def generation_interval(time: float) -> float:
    """Равномерное распределение меток с заданным временем time"""
    return time