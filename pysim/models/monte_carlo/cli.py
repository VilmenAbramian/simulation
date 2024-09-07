import click

from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)
from pysim.models.monte_carlo.objects import Config
from pysim.models.monte_carlo.handlers import initialize, finalize


MODEL_NAME = 'Monte-Carlo-simulation'
DEFAULT_PROBABILITY = (1, 1, 1, 1)
DEFAULT_PROCESSING_TIME = (1, 1, 1, 1)
DEFAULT_MAX_TRANSMISSIONS = 200000
DEFAULT_CHUNKS_NUMBER = 10
DEFAULT_SCENARIO = 3
SCENARIOS_TUPLE = (1, 2, 3)


@click.command()
@click.option(
    '-p', '--probability', nargs=4, type=click.Tuple(
        [float, float, float, float]
    ),
    default=DEFAULT_PROBABILITY,
    help='Массив вероятностей перехода из одного состояния в другое',
    show_default=True
)
@click.option(
    '-t', '--processing_time', nargs=4, type=click.Tuple(
        [float, float, float, float]
    ),
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
    help='Количество "чанков", на которые разбито состояние Secured',
    show_default=True
)
@click.option(
    '-s', '--scenario', default=DEFAULT_SCENARIO,
    help='Выбор одного из 3х сценариев моделирования',
    show_default=True
)
def cli_run(**kwargs):
    '''
    Точка входа модели.
    Задать параметры работы.
    '''
    if kwargs['scenario'] not in SCENARIOS_TUPLE:
        raise AttributeError('Недопустимый номер сценария!')
    if kwargs['scenario'] == 3 and kwargs['chunks_number'] < 1:
        raise AttributeError('Недопустимое количество "чанков"!')

    print(f'Running {MODEL_NAME} model. Scenario number {kwargs['scenario']}')
    print('Входные параметры: ', kwargs)
    result = run_model(Config(
        probability=kwargs['probability'],
        processing_time=kwargs['processing_time'],
        max_transmisions=kwargs['max_transmisions'],
        chunks_number=kwargs['chunks_number'],
        scenario=kwargs['scenario']
    ), ModelLoggerConfig())
    print('Суммарное время: ', result.sim_time)
    print('Среднее время до поглощения: ',
          result.sim_time/kwargs['max_transmisions'])


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
