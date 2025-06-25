from time import perf_counter
from typing import Any, Dict, List

from pydantic import BaseModel, Field
import click
import multiprocessing

import pysim.models.rfid.configurator as configurator
from pysim.models.rfid.params import (
    default_params, multipliers, inner_params
)
from pysim.models.rfid.processing import result_processing
import pysim.sim.simulator as sim


class SimulationResult(BaseModel):
    """Результаты симуляции одной RFID модели."""
    rounds_per_tag: float = Field(
        ..., description="Среднее количество раундов на одну метку"
    )
    inventory_prob: float = Field(
        ..., description="Вероятность успешной идентификации метки"
    )
    read_tid_prob: float = Field(
        ..., description="Вероятность успешного чтения банка памяти USER"
    )
    read_tid_time: float = Field(
        ..., description="Среднее время чтения банка памяти USER (в секундах)"
    )
    avg_collisions: float = Field(
        ..., description="Среднее количество коллизий для одной метки"
    )
    execution_time: float = Field(
        ..., description="Реальное время выполнения симуляции (в секундах)"
    )


def build_external_params(
        params: Dict[str, Any],
        parse_encoding: bool = False
) -> Dict[str, Any]:
    """
    Подготовить изменяемые из внешних источников параметры модели.

    В разных функциях данные требуются в отличающихся форматах, в связи
    с этим в функцию добавлены условия.

    Args:
        params - словарь с произвольными входными данными
        parse_encoding - флаг, от которого зависит формат возвращаемых данных

    Returns:
        Словарь с параметрами для запуска.
    """
    params_dict = {
        "speed": params.get("speed", default_params.speed),
        "encoding": params.get("encoding", default_params.encoding),
        "tari": float(params.get("tari", default_params.tari)),
        "tid_word_size": params.get(
            "tid_word_size", default_params.tid_word_size
        ),
        "reader_offset": params.get(
            "reader_offset", default_params.reader_offset
        ),
        "tag_offset": params.get("tag_offset", default_params.tag_offset),
        "altitude": params.get("altitude", default_params.altitude),
        "power": params.get("power", default_params.power_dbm),
        "num_tags": params.get("num_tags", default_params.num_tags),
        "useadjust": params.get("useadjust", default_params.useadjust),
        "q": params.get("q", default_params.q),
        "generation_interval": params.get(
            "generation_interval", inner_params.tag_params.generation_interval
        ),
    }
    if parse_encoding:
        params_dict["speed"] = params_dict["speed"] * multipliers.KMPH_TO_MPS
        params_dict["encoding"] = (
            default_params.parse_tag_encoding(params["encoding"])
        )
        params_dict["tari"] = params_dict["tari"] * multipliers.MICROSEC_TO_SEC
    return params_dict


@click.group()
def cli():
    pass


@cli.command("start")
@click.option(
    "-s", "--speed", multiple=True,
    default=(default_params.speed,),
    help="Vehicle speed, kmph. You can provide multiple values, e.g. "
         "`-s 10 -s 20 -s 80` for parallel computation.",
    show_default=True,
)
@click.option(
    "-m", "--encoding", type=click.Choice(["FM0", "M2", "M4", "M8"]),
    default=default_params.encoding, help="Tag encoding", show_default=True
)
@click.option(
    "-t", "--tari", default=str(default_params.tari), show_default=True,
    type=click.Choice(["6.25", "12.5", "18.75", "25"]), help="Tari value"
)
@click.option(
    "-ws", "--tid-word-size", multiple=True,
    default=(default_params.tid_word_size,),
    help="Size of TID bank in words (x16 bits). This is both TID bank "
         "size and the number of words the reader requests from the tag. "
         "You can provide multiple values for this parameter for parallel "
         "computation.", show_default=True,
)
@click.option(
    "-a", "--altitude", multiple=True, default=(default_params.altitude,),
    help="Drone with RFID-reader altitude. You can pass multiple values of "
         "this parameter for parallel computation.", show_default=True
)
@click.option(
    "-ro", "--reader-offset", multiple=True,
    default=(default_params.reader_offset,),
    help="Reader offset from the wall. You can pass multiple values of this "
         "parameter for parallel computation.", show_default=True,
)
@click.option(
    "-to", "--tag-offset", multiple=True, default=(default_params.tag_offset,),
    help="Tag offset from the wall. You can pass multiple values of this "
         "parameter for parallel computation.", show_default=True
)
@click.option(
    "-p", "--power", multiple=True, default=(default_params.power_dbm,),
    help="Reader transmitter power. You can pass multiple values of this "
         "parameter for parallel computation.", show_default=True
)
@click.option(
    "-n", "--num-tags", default=default_params.num_tags, show_default=True,
    help="Number of tags to simulate."
)
@click.option(
    "-ua", "--useadjust", is_flag=True, default=default_params.useadjust,
    show_default=True, help="Use QueryAdjust command for correct Q"
)
@click.option(
    "-q", "--q_value", default=default_params.q, show_default=True,
    help="Q param for slot counting"
)
def cli_run(**console_params):
    """
    Точка входа модели RFID при запуске через консоль.

    После выполнения моделей запускается обработка результатов в модуле
    processing.py.

    Args:
        console_params - словарь с входными параметрами в модель.
          Может быть задан через консольный click-интерфейс либо применяются
          параметры по умолчанию.
    """
    console_params, variadic = check_vars_for_multiprocessing(**console_params)
    print(f"Запуск {inner_params.model_name} модели")

    if variadic is None:
        result = prepare_simulation(console_params)
    else:
        result = prepare_multiple_simulation(variadic, **console_params)
    result_processing(console_params, result, variadic)


def check_vars_for_multiprocessing(**kwargs):
    """
    Проверка, указан ли какой-то параметр несколько раз.
    Если такой есть и он один, то выполним несколько симуляций параллельно.
    Если все параметры даны в одном экземпляре, то выполним одну симуляцию.
    Если несколько параметров заданы со множеством значений, это ошибка.
    """
    var_arg_names = (
        "speed", "tid_word_size", "altitude", "reader_offset",
        "tag_offset", "power", "q"
    )
    variadic = None
    for arg_name in var_arg_names:
        if len(kwargs[arg_name]) > 1:
            if variadic is not None:
                raise ValueError("Only one argument can have multiple values, "
                      f"not both \"{variadic}\" and \"{arg_name}\"")
            variadic = arg_name
        else:
            kwargs[arg_name] = kwargs[arg_name][0]
    return kwargs, variadic


def prepare_multiple_simulation(
        variadic: str,
        **kwargs
) -> List[SimulationResult]:
    """
    Какой-то параметр варьируется. Запускаем параллельно
    расчеты через пул рабочих.
    Убираем дубликаты и сортируем по возрастанию
    значения аргумента, по которому варьируемся.

    Args:
        variadic - название переменной, для которой передаётся
          несколько значений;
        kwargs - в этот словарь собираются все дополнительно переданные
          параметры для симуляции.

    Returns:
        Список с объектами-результатами работы симуляций (SimulationResult).
    """
    variadic_values = sorted(set(kwargs[variadic]))

    # Построим массив из копий параметров с заменой варьируемого значения
    args_list = []
    for value in variadic_values:
        params = build_external_params(kwargs)
        params[variadic] = value
        args_list.append(params)

    # Теперь заменим значения варьируемого аргумента, чтобы в каждом
    # элементе args хранилось только одно значение вместо всего набора.
    # for i, value in enumerate(variadic_values):
    #     args_list[i][variadic] = value

    pool = multiprocessing.Pool(
        kwargs.get("jobs", multiprocessing.cpu_count())
    )
    return pool.map(prepare_simulation, args_list)


def prepare_simulation(
        params: Dict[str, Any],
) -> SimulationResult:
    """
    Запускает одну имитационную симуляцию RFID-модели с заданными параметрами.

    Args:
        params: словарь параметров симуляции из списка params.RFIDDefaults.
          Эти параметры пользователь может переопределить через
          click-интерфейс.

    Returns:
        Результаты моделирования в Pydantic схеме
    """

    model_params = build_external_params(params, parse_encoding=True)
    model = configurator.create_model(**model_params)
    t_start = perf_counter()
    configurator.run_model(model, sim.ModelLoggerConfig())
    t_end = perf_counter()

    return SimulationResult(
        rounds_per_tag = model.statistics.average_rounds_per_tag(),
        inventory_prob = model.statistics.inventory_probability(),
        read_tid_prob = model.statistics.read_tid_probability(),
        read_tid_time = model.statistics.average_identification_time(),
        avg_collisions = model.statistics.average_collisions_per_tag(),
        execution_time = t_end - t_start
    )


if __name__ == "__main__":
    cli()
