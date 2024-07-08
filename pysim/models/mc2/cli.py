import click

from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)
from pysim.models.mc2.objects import Config
from pysim.models.mc2.handlers import initialize, finalize


MODEL_NAME = 'Monte-Carlo-2-scenario'
DEFAULT_PROBABILITY = (0.9, 0.91, 0.92, 0.93)
DEFAULT_PROCESSING_TIME = (0.01, 0.011, 0.012, 0.013)
DEFAULT_MAX_TRANSMISSIONS = 10


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
def cli_run(**kwargs):
    '''
    Точка входа модели.
    Задать параметры работы.
    '''
    print(f'Running {MODEL_NAME} model')
    print('Входные параметры: ', kwargs)
    result = run_model(Config(
        probability=kwargs['probability'],
        processing_time=kwargs['processing_time'],
        max_transmisions=kwargs['max_transmisions'],
    ), ModelLoggerConfig())
    print('Суммарное время: ', result.sim_time)
    print('Среднее время до поглощения: ', result.sim_time/kwargs['max_transmisions'])


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
