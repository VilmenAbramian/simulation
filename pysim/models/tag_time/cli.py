import click
from multiprocessing import Pool
import multiprocessing

from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)
from pysim.models.tag_time.objects import Config
from pysim.models.tag_time.handlers import initialize, finalize


MODEL_NAME = "Monte-Carlo-simulation"
DEFAULT_PROBABILITY = ((0.9, 0.95, 0.93, 0.91),)
DEFAULT_PROCESSING_TIME = ((1, 1, 1, 1),)
DEFAULT_MAX_TRANSMISSIONS = 2000
DEFAULT_CHUNKS_NUMBER = 10
DEFAULT_SCENARIO = 1
SCENARIOS_TUPLE = (1, 2, 3)


def check_vars(**kwargs):
    """
    Проверка корректности введённых аргументов и
    выбор режима работы симуляции (одиночный или
    несколько моделей одновременно)
    """
    if kwargs['scenario'] not in SCENARIOS_TUPLE:
        raise AttributeError('Недопустимый номер сценария!')
    if kwargs['scenario'] == 3 and kwargs['chunks_number'] < 1:
        raise AttributeError('Недопустимое количество "чанков"!')
    if len(kwargs['probability']) != len(kwargs['processing_time']):
        raise AttributeError(
            'Количество массивов времени и вероятностей не совпадает!'
        )

    if (len(kwargs['probability']) > 1 and
           (type(kwargs['probability'][0]) is tuple)):
        mode = 'plural'
    else:
        mode = 'single'
    return mode


@click.command()
@click.option(
    '-p', '--probability', nargs=4, type=click.Tuple(
        [float, float, float, float]
    ),
    multiple=True,
    default=DEFAULT_PROBABILITY,
    help='Массив вероятностей перехода из одного состояния в другое',
    show_default=True
)
@click.option(
    '-t', '--processing_time', nargs=4, type=click.Tuple(
        [float, float, float, float]
    ),
    multiple=True,
    default=DEFAULT_PROCESSING_TIME,
    help='Массив длительностей обработки пакета в каждом из состояний',
    show_default=True
)
@click.option(
    '-m', '--max_transmisions', default=DEFAULT_MAX_TRANSMISSIONS,
    help='Количество отправляемых пакетов',
    show_default=True
)
@click.option(
    '-cn', '--chunks_number', default=DEFAULT_CHUNKS_NUMBER,
    help='Количество частей, на которые разбито состояние Secured',
    show_default=True
)
@click.option(
    '-s', '--scenario', default=DEFAULT_SCENARIO,
    help='Выбор одного из 3х сценариев моделирования',
    show_default=True
)
def cli_run(**kwargs):
    """
    Точка входа модели.
    Задать параметры работы.
    """
    mode = check_vars(**kwargs)
    print(f'Running {MODEL_NAME} model. Scenario number {kwargs["scenario"]}')
    print('Входные параметры: ', kwargs)
    if mode == 'single':
        kwargs['probability'] = kwargs['probability'][0]
        kwargs['processing_time'] = kwargs['processing_time'][0]
        result = create_config(kwargs)
    else:
        result = run_multiple_simulation(kwargs)
    print(result)
    return result
    # result_processing(kwargs, result)


def create_config(kwargs):
    # print(f'Что пришло на вход: {kwargs}')
    return run_model(Config(
        probability=kwargs['probability'],
        processing_time=kwargs['processing_time'],
        max_transmisions=kwargs['max_transmisions'],
        chunks_number=kwargs['chunks_number'],
        scenario=kwargs['scenario']
    ), ModelLoggerConfig())


def run_multiple_simulation(kwargs):
    # Построим массив из копий параметров
    args_list = [{
        'probability': kwargs['probability'][i],
        'processing_time': kwargs['processing_time'][i],
        'max_transmisions': kwargs['max_transmisions'],
        'chunks_number': kwargs['chunks_number'],
        'scenario': kwargs['scenario'],
    } for i in range(len(kwargs['probability']))]

    pool = Pool(kwargs.get('jobs', multiprocessing.cpu_count()))
    return pool.map(create_config, args_list)


def run_model(
    config: Config,
    logger_config: ModelLoggerConfig,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None,
):
    result, context, fin_ret = run_simulation(
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


if __name__ == '__main__':
    cli_run()
