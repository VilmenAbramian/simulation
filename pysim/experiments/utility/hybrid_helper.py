# ##################################################
# Функции для запуска моделирования и построения графиков для
# имитационной модели гибридной системы.
#
# Используется в блокноте:
# hybrid.ipynb
# ##################################################
from typing import Any
import json

from tqdm.notebook import tqdm
import matplotlib.pyplot as plt
import os

from pysim.experiments.utility.graphs_style import savefig, setup_matplotlib
from pysim.experiments.utility.rfid_helper import convert_non_serializable
from pysim.models.hybrid.cli import run_multiple_simulation
from pysim.models.hybrid.processing import result_processing


setup_matplotlib()

IMAGE_DIRECTORY = "hybrid/"
JSON_DIRECTORY = "../results/result_jsons/hybrid/"
SAVE_FIG = True          # Сохранять ли изображения
SAVE_RESULTS = False      # Сохранять ли результаты в JSON
USE_JSON = True          # Использовать ли результаты из JSON


class Consts:
    NUM_POINTS = 25
    NUM_LINES = 5

class Probs:
    MIN_ERROR_CAM_PROB = 0
    MAX_ERROR_CAM_PROB = 1
    MIN_ERROR_RFID_PROB = 0
    MAX_ERROR_RFID_PROB = 1



def plate_to_symbol_error(prob: float, symbols_in_plate: int) -> float:
    """
    Преобразование вероятности ошибки идентификации номера в
    вероятность ошибки идентификации одного символа в номере.
    """
    return 1 - (1 - prob) ** (
            1 / symbols_in_plate
    )


def get_experiments_results(
    variadic: str,
    variadic_values: list[float],
    line_variable: str,
    line_variable_values: list[float],
    params_list: list[dict[str, Any]],
    result_param_name: str,
    use_json: bool = USE_JSON,
    save_results: bool = SAVE_RESULTS,
    json_directory: str = JSON_DIRECTORY,
    file_name: str = "probs.json",
) -> list[list[float]]:
    """
    Возвращает результаты работы нескольких последовательных пакетов имитационок.

    Данные могут быть как прочитаны из json-файла, так и вычислены снова
    (что требует длительного ожидания). Также имеется возможность сохранить
    вычисленные значения в json-файл для дальнейшего ускорения работы.

    Args:
    variadic: название параметра, изменяющегося внутри одной кривой;
    variadic_values: значения параметра для одной кривой;
    line_variable: название параметра, который меняется для каждой кривой;
    line_variable_values: значения параметра для разных кривых (как правило, около 5 значений);
    params_list: входные параметры для нескольких кривых;
    result_param_name: название поля pydantic-объекта Results, в котором хранятся требуемые значения;
    use_json: если True, то попытаться загрузить результаты из JSON;
    save_results: если True, сохранить результаты в JSON;
    json_directory: директория сохранения результатов в JSON;
    file_name: имя файла JSON.
    """
    directory = json_directory + file_name
    results_list = []

    if use_json and os.path.exists(directory):
        with open(directory, "r") as f:
            data = json.load(f)
            if "Results" not in data:
                raise ValueError(
                    f"Файл {directory} не содержит блока 'Results'"
                )
            results_list = data["Results"]
    else:
        for params in tqdm(
                params_list, desc=f"Моделирование по переменной {variadic}",
                unit="кривая"
        ):
            statistica = run_multiple_simulation(variadic, **params)
            results_list.append(result_processing(params, statistica, variadic, print_res=False))

    res_probs = []
    for line in results_list:
        line_probs = []
        for res in line:
            # Поддержка Pydantic и dict
            value = getattr(
                res, result_param_name, None
            ) if not isinstance(res, dict) else res.get(result_param_name)
            line_probs.append(value)
        res_probs.append(line_probs)

    if save_results:
        save_json_results(
            directory, line_variable, line_variable_values, variadic,
            variadic_values, params_list, results_list
        )
    return res_probs


def save_json_results(
        directory: str,
        line_variable: str,
        line_variable_values: list[float],
        variadic: str,
        variadic_values: list[float],
        params_list: list,
        results_list: list,
) -> None:
    """
    Args:
        directory: путь, в котором будут сохраняться результаты;
        line_variable: название параметра, который меняется для каждой кривой;
        line_variable_values: значения параметра для разных кривых (как правило, около 5 значений);
        variadic: Название параметра, изменяющегося внутри одной кривой;
        variadic_values: значения параметра для одной кривой;
        params_list: входные параметры для нескольких кривых;
        results_list: результаты моделирования для нескольких кривых.

    """
    os.makedirs(os.path.dirname(directory), exist_ok=True)
    with open(directory, "w", encoding="utf-8") as f:
        json.dump({
            f"Значение {line_variable} для каждой кривой": line_variable_values,
            f"Изменяющаяся переменная одной кривой {variadic}": variadic_values,
            f"Входные параметры модели: {params_list}": params_list,
            "Results": [
                [res.model_dump() for res in result_sublist]
                for result_sublist in results_list
            ]
        }, f, ensure_ascii=False, indent=2, default=convert_non_serializable)


def plot_experiment_lines(
    x_values: list[float],
    y_lines: list[list[float]],
    labels: list[str],
    xlabel: str,
    ylabel: str,
    title: str,
    image_name: str = "Probs",
    image_directory: str = IMAGE_DIRECTORY,
    save_fig: bool = SAVE_FIG,
    inversion: bool = True
):
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    for i, (y, label) in enumerate(zip(y_lines, labels)):
        if inversion:
            y = y[::-1]
        ax.plot(
            x_values, y,
            linewidth=3, linestyle="dashdot",
            label=label,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tick_params(axis="both", which="major")
    plt.title(title)
    plt.legend(prop={"size":15})
    plt.grid()

    if save_fig:
        savefig(name=image_name, directory=image_directory)
