import click
from multiprocessing import Pool
import multiprocessing


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
    result_processing(kwargs, result, variadic)


if __name__ == '__main__':
    cli_run()
