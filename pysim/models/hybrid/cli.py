import click
from multiprocessing import Pool
import multiprocessing
from typing import List

from pysim.models.hybrid.handlers import initialize, finalize
from pysim.models.hybrid.objects import Params, Results, Statistic
from pysim.models.hybrid.processing import result_processing
from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)


def check_vars_for_multiprocessing(**kwargs):
    """
    Проверка, указан ли какой-то параметр несколько раз.
    Если такой есть и он один, то выполним несколько симуляций параллельно.
    Если все параметры даны в одном экземпляре, то выполним одну симуляцию.
    Если несколько параметров заданы со множеством значений, это ошибка.
    """
    var_arg_names = ("photo_error", "rfid_error", "car_error",
                     "speed", "transport_gap")
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


def run_multiple_simulation(variadic, **kwargs)-> List[Results]:
    """
    Какой-то параметр варьируется. Запускаем параллельно расчеты через
    пул рабочих.
    Убираем дубликаты и сортируем по возрастанию значения аргумента,
    по которому варьируемся.
    """
    variadic_values = sorted(set(kwargs[variadic]))

    # Создаём копию kwargs для каждого значения параметра
    args_list = [kwargs.copy() for _ in variadic_values]

    # Подставляем уникальное значение параметра в каждый набор аргументов
    for i, value in enumerate(variadic_values):
        args_list[i][variadic] = value

    pool = Pool(kwargs.get("jobs", multiprocessing.cpu_count()))
    return pool.map(create_config, args_list)


@click.command()
@click.option(
    "-n", "--num-plates", default=Params().num_plates,
    help="Количество идентифицируемых автомобилей",
    show_default=True
)
@click.option(
    "-pd", "--photo-distance", nargs=2, type=click.Tuple([float, float]),
    default=Params().photo_distance,
    help="Зона видимости камеры в метрах",
    show_default=True
)
@click.option(
    "-rd", "--rfid-distance", nargs=2, type=click.Tuple([float, float]),
    default=Params().rfid_distance,
    help="Зона видимости RFID считывателя в метрах",
    show_default=True
)
@click.option(
    "-s", "--speed", nargs=2, type=click.Tuple([float, float]),
    default=(Params().speed_range, ), multiple=True,
    help="Диапазон скоростей движения машин в метрах в секунду",
    show_default=True
)
@click.option(
    "-d", "--transport-gap", default=(Params().transport_distance, ),
    multiple=True, help="Расстояние между машинами в метрах",
    show_default=True
)
@click.option(
    "-pe", "--photo-error", default=(Params().symbol_error, ), multiple=True,
    help="Вероятность ошибки идентификации номерной таблички камерой",
    show_default=True
)
@click.option(
    "-re", "--rfid-error", default=(Params().rfid_error, ), multiple=True,
    help="Вероятность ошибки идентификации ТС RFID системой",
    show_default=True
)
@click.option(
    "-ce", "--car-error", default=(Params().car_error, ), multiple=True,
    help="Вероятность ошибки идентификации модели машины камерой",
    show_default=True
)
def cli_run(**kwargs):
    """
    Точка входа модели гибридной системы идентификации.
    Задать параметры работы.
    """
    kwargs, variadic = check_vars_for_multiprocessing(**kwargs)
    print(f"Running {Params().model_name} model")
    if variadic is None:
        model_result = create_config(kwargs)
    else:
        model_result = run_multiple_simulation(variadic, **kwargs)

    return result_processing(kwargs, model_result, variadic, print_res=False)


def create_config(*args) -> Statistic:
    kwargs = args[0]
    return run_model(Params(
        sign_prob=Params().sign_prob,
        num_prob=Params().num_prob,
        num_plates=kwargs["num_plates"],
        speed_range=kwargs["speed"],
        transport_distance=kwargs["transport_gap"],
        photo_distance=kwargs["photo_distance"],
        rfid_distance = kwargs["rfid_distance"],
        photo_error = kwargs["photo_error"],
        rfid_error = kwargs["rfid_error"],
        car_error = kwargs["car_error"],
    ), ModelLoggerConfig())

def run_model(
    config: Params,
    logger_config: ModelLoggerConfig,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None,
) -> Statistic:
    sim_time, _, result = run_simulation(
        build_simulation(
            Params().model_name,
            init=initialize,
            init_args=(config,),
            fin=finalize,
            max_real_time=max_real_time,
            max_sim_time=max_sim_time,
            max_num_events=max_num_events,
            logger_config=logger_config
        ))
    return result


if __name__ == "__main__":
    cli_run()
