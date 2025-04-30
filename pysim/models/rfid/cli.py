import click
import multiprocessing
from time import time_ns

import pysim.models.rfid.configurator as configurator
import pysim.models.rfid.epcstd as std
from pysim.models.rfid.processing import result_processing
import pysim.sim.simulator as sim


DEFAULT_SPEED = 25             # kmph
DEFAULT_ENCODING = '2'         # FM0, M2, M4, M8
DEFAULT_TARI = '12.5'          # 6.25, 12.5, 18.75, 25
DEFAULT_TID_WORD_SIZE = 64     # number of words to read from TID (=1024 bits)
DEFAULT_READER_OFFSET = 3.0    # meters from the wall
DEFAULT_TAG_OFFSET = 2.0       # meters from the wall
DEFAULT_ALTITUDE = 5.0
DEFAULT_NUM_TAGS = 40          # Количество генерируемых меток
DEFAULT_POWER = 29
USE_QUERY_ADJUST = False       # Использовать ли QueryAdjust
DEFAULT_ADJUST_DELTA = 0.5     # Значение для корректировки Q в QueryAdjust


# ----------------------------------------------------------------------------
@click.group()
def cli():
    pass


@cli.command('start')
@click.option(
    '-s', '--speed', default=(DEFAULT_SPEED,), multiple=True,
    help='Vehicle speed, kmph. You can provide multiple values, e.g. '
         '`-s 10 -s 20 -s 80` for parallel computation.',
    show_default=True,
)
@click.option(
    '-m', '--encoding', type=click.Choice(['1', '2', '4', '8']),
    default=DEFAULT_ENCODING, help='Tag encoding', show_default=True
)
@click.option(
    '-t', '--tari', default=DEFAULT_TARI, show_default=True,
    type=click.Choice(['6.25', '12.5', '18.75', '25']), help='Tari value'
)
@click.option(
    '-ws', '--tid-word-size', default=(DEFAULT_TID_WORD_SIZE,), multiple=True,
    help='Size of TID bank in words (x16 bits). This is both TID bank '
         'size and the number of words the reader requests from the tag. '
         'You can provide multiple values for this parameter for parallel '
         'computation.', show_default=True,
)
@click.option(
    '-a', '--altitude', multiple=True, default=(DEFAULT_ALTITUDE,),
    help='Drone with RFID-reader altitude. You can pass multiple values of '
         'this parameter for parallel computation.', show_default=True
)
@click.option(
    '-ro', '--reader-offset', default=(DEFAULT_READER_OFFSET,), multiple=True,
    help='Reader offset from the wall. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True,
)
@click.option(
    '-to', '--tag-offset', default=(DEFAULT_TAG_OFFSET,), multiple=True,
    help='Tag offset from the wall. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True
)
@click.option(
    '-p', '--power', default=(DEFAULT_POWER,), multiple=True,
    help='Reader transmitter power. You can pass multiple values of this '
         'parameter for parallel computation.', show_default=True
)
@click.option(
    '-n', '--num-tags', default=DEFAULT_NUM_TAGS, show_default=True,
    help='Number of tags to simulate.'
)
@click.option(
    '-v', '--verbose', is_flag=True, default=False, show_default=True,
    help='Print additional data, e.g. detailed model configuration.'
)
@click.option(
    '-ua', '--useadjust', is_flag=True, default=USE_QUERY_ADJUST,
    show_default=True, help='Use QueryAdjust command for correct Q'
)
@click.option(
    '-d', '--delta', default=DEFAULT_ADJUST_DELTA, show_default=True,
    help='Coefficient for QueryAdjust algorithm'
)
def cli_run(**kwargs):
    '''
    Точка входа модели RFID.
    Задать параметры модели.
    '''
    kwargs, variadic = check_vars_for_multiprocessing(**kwargs)
    print(f'Running {configurator.MODEL_NAME} model')

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


def prepare_simulation(kwargs):
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
        encoding = parse_tag_encoding(kwargs['encoding'])
    except ValueError:
        pass
    model = configurator.create_model(
        speed=(kwargs['speed'] * configurator.KMPH_TO_MPS_MUL),
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
    print(
        'Статистика: ', model.statistics.average_changing_q()
    )
    return (result, ((t_end_ns - t_start_ns) / 1_000_000_000))


def parse_tag_encoding(s):
    s = s.upper()
    if s in {'1', "FM0"}:
        return std.TagEncoding.FM0
    elif s in {'2', 'M2'}:
        return std.TagEncoding.M2
    elif s in {'4', 'M4'}:
        return std.TagEncoding.M4
    elif s in {'8', 'M8'}:
        return std.TagEncoding.M8
    else:
        raise ValueError('illegal encoding = {}'.format(s))


if __name__ == '__main__':
    cli()
