from time import perf_counter
from typing import Any, Dict, Literal , Tuple

from pydantic import BaseModel, Field
import click
import multiprocessing

import pysim.models.rfid.configurator as configurator
from pysim.models.rfid.params import (
    KMPH_TO_MPS_MUL, default_params, inner_params
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
    execution_time: float = Field(
        ..., description="Время выполнения симуляции (в секундах)"
    )


@click.group()
def cli():
    pass


@cli.command('start')
@click.option(
    '-s', '--speed', multiple=True,
    default=(default_params.speed,),
    help='Vehicle speed, kmph. You can provide multiple values, e.g. '
         '`-s 10 -s 20 -s 80` for parallel computation.',
    show_default=True,
)
@click.option(
    '-m', '--encoding', type=click.Choice(['FM0', 'M2', 'M4', 'M8']),
    default=default_params.encoding, help='Tag encoding', show_default=True
)
@click.option(
    '-t', '--tari', default=str(default_params.tari), show_default=True,
    type=click.Choice(['6.25', '12.5', '18.75', '25']), help='Tari value'
)
@click.option(
    '-ws', '--tid-word-size', multiple=True,
    default=(default_params.tid_word_size,),
    help='Size of TID bank in words (x16 bits). This is both TID bank '
         'size and the number of words the reader requests from the tag. '
         'You can provide multiple values for this parameter for parallel '
         'computation.', show_default=True,
)
@click.option(
    '-a', '--altitude', multiple=True, default=(default_params.altitude,),
    help='Drone with RFID-reader altitude. You can pass multiple values of '
         'this parameter for parallel computation.', show_default=True
)
@click.option(
    '-ro', '--reader-offset', multiple=True,
    default=(default_params.reader_offset,),
    help='Reader offset from the wall. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True,
)
@click.option(
    '-to', '--tag-offset', multiple=True, default=(default_params.tag_offset,),
    help='Tag offset from the wall. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True
)
@click.option(
    '-p', '--power', multiple=True, default=(default_params.power_dbm,),
    help='Reader transmitter power. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True
)
@click.option(
    '-n', '--num-tags', default=default_params.num_tags, show_default=True,
    help='Number of tags to simulate.'
)
@click.option(
    '-v', '--verbose', is_flag=True, default=False, show_default=True,
    help='Print additional data, e.g. detailed model configuration.'
)
@click.option(
    '-ua', '--useadjust', is_flag=True, default=default_params.useadjust,
    show_default=True, help='Use QueryAdjust command for correct Q'
)
@click.option(
    '-q', '--q_value', default=default_params.q, show_default=True,
    help='Q param for slot counting'
)
def cli_run(**kwargs):
    '''
    Точка входа модели RFID.
    Задать параметры модели.
    '''
    kwargs, variadic = check_vars_for_multiprocessing(**kwargs)
    print(f'Запуск {inner_params.model_name} модели')

    if variadic is None:
        result = prepare_simulation(kwargs)
    else:
        result = prepare_multiple_simulation(variadic, **kwargs)
    result_processing(kwargs, result, variadic)


def check_vars_for_multiprocessing(**kwargs):
    '''
    Проверка, указан ли какой-то параметр несколько раз.
    Если такой есть и он один, то выполним несколько симуляций параллельно.
    Если все параметры даны в одном экземпляре, то выполним одну симуляцию.
    Если несколько параметров заданы со множеством значений, это ошибка.
    '''
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


def prepare_multiple_simulation(variadic, **kwargs):
    '''
    Какой-то параметр варьируется. Запускаем параллельно
    расчеты через пул рабочих.
    Убираем дубликаты и сортируем по возрастанию
    значения аргумента, по которому варьируемся.
    '''
    variadic_values = sorted(set(kwargs[variadic]))

    # Построим массив из копий параметров
    args_list = [{
        'speed': kwargs['speed'],
        'tari': kwargs['tari'],
        'encoding': kwargs['encoding'],
        'tid_word_size': kwargs['tid_word_size'],
        'reader_offset': kwargs['reader_offset'],
        'tag_offset': kwargs['tag_offset'],
        'altitude': kwargs['altitude'],
        'power': kwargs['power'],
        'num_tags': kwargs['num_tags'],
        'verbose': False,
        'useadjust': kwargs.get('useadjust', False),
        'q': kwargs.get('q'),
    } for _ in enumerate(variadic_values)]

    # Теперь заменим значения варьируемого аргумента, чтобы в каждом
    # элементе args хранилось только одно значение вместо всего набора.
    for i, value in enumerate(variadic_values):
        args_list[i][variadic] = value

    pool = multiprocessing.Pool(
        kwargs.get('jobs', multiprocessing.cpu_count())
    )
    return pool.map(prepare_simulation, args_list)


def prepare_simulation(
        params: Dict[str, Any],
        show_params: bool = False
) -> SimulationResult:
    """
    Запускает одну имитационную симуляцию RFID-модели с заданными параметрами.

    Args:
        params: Словарь параметров симуляции из списка params.RFIDDefaults;
        show_params: Если True, выводит параметры запуска в консоль.

    Returns:
        Результаты моделирования в Pydantic схеме
    """
    if show_params:
        print(f'[+] Estimating speed = {params["speed"]} kmph, '
              f'Tari = {params["tari"]} us, '
              f'M = {params["encoding"]}, '
              f'tid_size = {params["tid_word_size"]} words, '
              f'reader_offset = {params["reader_offset"]} m, '
              f'tag_offset = {params["tag_offset"]} m, '
              f'altitude = {params["altitude"]} m,'
              f'power = {params["power"]} dBm, '
              f'num_tags = {params["num_tags"]}')
    encoding = default_params.parse_tag_encoding(params['encoding'])
    model = configurator.create_model(
        speed=(params['speed'] * KMPH_TO_MPS_MUL),
        encoding=encoding,
        tari=float(params['tari']) * 1e-6,
        tid_word_size=params['tid_word_size'],
        reader_offset=params['reader_offset'],
        tag_offset=params['tag_offset'],
        altitude=params['altitude'],
        power=params['power'],
        num_tags=params['num_tags'],
        verbose=params['verbose'],
        useadjust=params['useadjust'],
        q=params['q']
    )
    t_start = perf_counter()
    configurator.run_model(model, sim.ModelLoggerConfig())
    t_end = perf_counter()

    return SimulationResult(
        rounds_per_tag = model.statistics.average_rounds_per_tag(),
        inventory_prob = model.statistics.inventory_probability(),
        read_tid_prob = model.statistics.read_tid_probability(),
        execution_time = t_end - t_start
    )


if __name__ == '__main__':
    cli()
