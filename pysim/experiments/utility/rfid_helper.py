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
from typing import Any, Callable, Dict
import matplotlib.pyplot as plt

from pysim.experiments.utility.graphs_style import savefig, setup_matplotlib
from pysim.models.rfid.cli import prepare_multiple_simulation
from pysim.models.rfid.params import default_params, inner_params

setup_matplotlib()


IMAGE_DIRECTORY = "rfid/"
JSON_DIRECTORY = "results/result_jsons/rfid/"
SAVE_FIG = False         # Сохранять ли изображения
SAVE_RESULTS = False     # Сохранять ли результаты в JSON
USE_JSON = True          # Использовать ли результаты из JSON


def calculate_probs(
    variable: str,
    variable_values: list,
    params_list: list[dict],
    key_fn: Callable[[dict], str],
    additional_params: Dict[str, Any] | None = None,
    use_json: bool = USE_JSON,
    save_results: bool = SAVE_RESULTS,
    json_directory: str = JSON_DIRECTORY,
    file_name: str = "probs",
    manual_key: str | None = None,
) -> dict[str, list[float]]:
    """
    Запуск нескольких сетов моделирования и получение зависимостей
    вероятности чтения от варьируемого параметра.

    Args:
        variable: имя переменной, в зависимости от которой исследуется вероятность;
        variable_values: список значений переменной variable (ось абсцисс);
        params_list: список параметров для разных кривых каждого сета моделирования;
        key_fn: функция, формирующая имя кривой по параметрам из params_list;
        additional_params: задаваемые из кода параметры (их нельзя ввести из
          click интерфейса);
        use_json: если True, то попытаться загрузить результаты из JSON;
        save_results: если True, сохранить результаты в JSON;
        json_directory: директория сохранения результатов в JSON;
        file_name: имя файла JSON.

    Returns:
        results: словарь, где ключ — имя кривой, значение — список вероятностей.
    """
    directory = json_directory + file_name
    collision_counts = {}
    rounds_count = {}
    if use_json and os.path.exists(directory):
        with open(directory, 'r') as f:
            results = json.load(f)
    else:
        results = {}
        for params in tqdm(params_list, desc=f"Моделирование по переменной {variable}"):
            sim_results = prepare_multiple_simulation(
                variable, additional_params,
                **{variable: variable_values}, **params
            )
            key = manual_key if manual_key is not None else key_fn(params)
            results[key] = [res.read_tid_prob for res in sim_results]
            collision_counts[key] = [res.avg_collisions for res in sim_results]
            rounds_count[key] = [res.rounds_per_tag for res in sim_results]
            print(f"Collisions: {collision_counts}")
            print(f"Rounds: {rounds_count}")

        if save_results:
            os.makedirs(os.path.dirname(directory), exist_ok=True)
            with open(directory, 'w') as f:
                json.dump(results, f, indent=2)
    return results


def plot_probs(
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


def generation_interval(time: float) -> float:
    """Равномерное распределение меток с заданным временем time"""
    return time