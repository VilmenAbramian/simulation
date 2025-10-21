import click
from multiprocessing import Pool
import multiprocessing

from pysim.models.hybrid.handlers import initialize, finalize
from pysim.models.hybrid.objects import Params, Result
from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)


MODEL_NAME = "Hybrid system simulation"
PHOTO_DISTANCE = (30, 50) # meters
RFID_DISTANCE = (-5, 5) # meters
SPEED = (60 / 3.6, 100 / 3.6) # kilometers per hour
DISTANCE_BETWEEN_TRANSPORTS = 10 # meters

PHOTO_ERROR = 0.1
RFID_ERROR = 0.05
CAR_ERROR = 0.1


def check_vars_for_multiprocessing(**kwargs):
    ...


def run_multiple_simulation(variadic, **kwargs):
    ...


@click.command()
@click.option(
    "-pd", "--photo-distance", nargs=2, type=click.Tuple([float, float]),
    default=PHOTO_DISTANCE,
    help="Зона видимости камеры в метрах???",
    show_default=True
)
@click.option(
    "-rd", "--rfid-distance", nargs=2, type=click.Tuple([float, float]),
    default=RFID_DISTANCE,
    help="Зона видимости RFID считывателя в метрах???",
    show_default=True
)
@click.option(
    "-s", "--speed", nargs=2, type=click.Tuple([float, float]),
    default=SPEED,
    help="Скорость движения в метрах в секунду???",
    show_default=True
)
@click.option(
    "-d", "--transport-gap", default=DISTANCE_BETWEEN_TRANSPORTS,
    help="Расстояние между ТС???",
    show_default=True
)
@click.option(
    "-pe", "--photo-error", default=PHOTO_ERROR,
    help="Вероятность ошибки идентификации ТС камерой???",
    show_default=True
)
@click.option(
    "-re", "--rfid-error", default=RFID_ERROR,
    help="Вероятность ошибки идентификации ТС RFID системой???",
    show_default=True
)
@click.option(
    "-ce", "--car-error", default=CAR_ERROR,
    help="Что это???",
    show_default=True
)
def cli_run(**kwargs):
    """
    Точка входа модели гибридной системы идентификации.
    Задать параметры работы.
    """
    variadic = None
    print(f'Running {MODEL_NAME} model')
    if variadic is None:
        result = create_config(kwargs)
    else:
        result = run_multiple_simulation(variadic, **kwargs)
    print("Конец")
    # result_processing(kwargs, result, variadic)


def create_config(*args):
    kwargs = args[0]
    return run_model(Params(
        sign_prob=kwargs["sign_prob"],
        num_prob=kwargs["num_prob"],
        average_speed=kwargs["average_speed"],
        transport_distance=kwargs["transport_distance"],
        photo_distance=kwargs["photo_distance"],
        rfid_distance = kwargs["rfid_distance"],
        photo_error = kwargs["photo_error"],
        rfid_error = kwargs["rfid_error"]
    ), ModelLoggerConfig())

def run_model(
    config: Params,
    logger_config: ModelLoggerConfig,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None,
) -> Result:
    sim_time, _, result = run_simulation(
        build_simulation(
            MODEL_NAME,
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
