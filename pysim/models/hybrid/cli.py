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


def check_vars_for_multiprocessing(**kwargs):
    ...


def run_multiple_simulation(variadic, **kwargs):
    ...


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
    default=Params().speed_range,
    help="Диапазон скоростей движения машин в метрах в секунду",
    show_default=True
)
@click.option(
    "-d", "--transport-gap", default=Params().transport_distance,
    help="Расстояние между машинами в метрах",
    show_default=True
)
@click.option(
    "-pe", "--photo-error", default=Params().symbol_error,
    help="Вероятность ошибки идентификации номерной таблички камерой",
    show_default=True
)
@click.option(
    "-re", "--rfid-error", default=Params().rfid_error,
    help="Вероятность ошибки идентификации ТС RFID системой",
    show_default=True
)
@click.option(
    "-ce", "--car-error", default=Params().car_error,
    help="Вероятность ошибки идентификации модели машины камерой",
    show_default=True
)
def cli_run(**kwargs):
    """
    Точка входа модели гибридной системы идентификации.
    Задать параметры работы.
    """
    # print(f"Входные параметры: {kwargs}")
    variadic = None
    print(f'Running {Params().model_name} model')
    if variadic is None:
        result = create_config(kwargs)
    else:
        result = run_multiple_simulation(variadic, **kwargs)
    print(len(result.clear_cam_detections)/kwargs["num_plates"])
    # result_processing(kwargs, result, variadic)


def create_config(*args):
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
) -> Result:
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
