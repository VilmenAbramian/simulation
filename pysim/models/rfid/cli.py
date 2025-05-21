import click
import multiprocessing
from time import time_ns

import pysim.models.rfid.configurator as configurator
from pysim.models.rfid.constants import (
    KMPH_TO_MPS_MUL, default_params, inner_params
)
from pysim.models.rfid.processing import result_processing
import pysim.sim.simulator as sim


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
    '-d', '--delta', default=default_params.delta, show_default=True,
    help='Coefficient for QueryAdjust algorithm'
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
        'speed', 'tid_word_size', 'altitude', 'reader_offset',
        'tag_offset', 'power'
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
        'delta': kwargs.get('delta', 0.5),
    } for _ in enumerate(variadic_values)]

    # Теперь заменим значения варьируемого аргумента, чтобы в каждом
    # элементе args хранилось только одно значение вместо всего набора.
    for i, value in enumerate(variadic_values):
        args_list[i][variadic] = value

    pool = multiprocessing.Pool(
        kwargs.get('jobs', multiprocessing.cpu_count())
    )
    return pool.map(prepare_simulation, args_list)


def prepare_simulation(kwargs, show_params=False):
    if show_params:
        print(f'[+] Estimating speed = {kwargs["speed"]} kmph, '
              f'Tari = {kwargs["tari"]} us, '
              f'M = {kwargs["encoding"]}, '
              f'tid_size = {kwargs["tid_word_size"]} words, '
              f'reader_offset = {kwargs["reader_offset"]} m, '
              f'tag_offset = {kwargs["tag_offset"]} m, '
              f'altitude = {kwargs["altitude"]} m, power = {kwargs["power"]} dBm, '
              f'num_tags = {kwargs["num_tags"]}')
    t_start_ns = time_ns()
    try:
        encoding = default_params.parse_tag_encoding(kwargs['encoding'])
    except ValueError:
        pass
    model = configurator.create_model(
        speed=(kwargs['speed'] * KMPH_TO_MPS_MUL),
        # speed=(kwargs['speed']),
        encoding=encoding,
        tari=float(kwargs['tari']) * 1e-6,
        tid_word_size=kwargs['tid_word_size'],
        reader_offset=kwargs['reader_offset'],
        tag_offset=kwargs['tag_offset'],
        altitude=kwargs['altitude'],
        power=kwargs['power'],
        num_tags=kwargs['num_tags'],
        verbose=kwargs['verbose'],
        useadjust=kwargs['useadjust'],
        delta=kwargs['delta']
    )
    configurator.run_model(model, sim.ModelLoggerConfig())
    t_end_ns = time_ns()
    result = {
        'rounds_per_tag': model.statistics.average_rounds_per_tag(),
        'inventory_prob': model.statistics.inventory_probability(),
        'read_tid_prob': model.statistics.read_tid_probability()
    }
    # print(
    #     'Статистика: ', model.statistics.average_changing_q()
    # )
    return (result, ((t_end_ns - t_start_ns) / 1_000_000_000))


if __name__ == '__main__':
    cli()
