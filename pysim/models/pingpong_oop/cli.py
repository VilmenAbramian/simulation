import click

from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)
from config import Config
from result import Result
from pysim.models.pingpong_oop.handlers import initialize, finalize

MODEL_NAME = 'PingPongOOP'
DEFAULT_INTERVAL = 10.0
DEFAULT_LOSS_PROB = 0.1
DEFAULT_CHANNEL_DELAY = 2.0
DEFAULT_SERVICE_DELAY = 1.0
MAX_PINGS = 1000000


@click.command()
@click.option(
    '-i', '--interval', default=DEFAULT_INTERVAL,
    help='Интервал отправки Ping клиентом (условные единицы)',
    show_default=True
)
@click.option(
    '-ch', '--channel_delay', default=DEFAULT_CHANNEL_DELAY,
    help='Длительность передачи сообщения (условные единицы)',
    show_default=True
)
@click.option(
    '-s', '--service_delay', default=DEFAULT_SERVICE_DELAY,
    help='Длительность обслуживания Ping',
    show_default=True
)
@click.option(
    '-l', '--loss_prob', default=DEFAULT_LOSS_PROB,
    help='Вероятность потери пакета в канале',
    show_default=True
)
@click.option(
    '-mp', '--max_pings', default=MAX_PINGS,
    help='Количество отправляемых клиентом Ping-ов',
    show_default=True
)
def cli_run(interval,
            channel_delay,
            service_delay,
            loss_prob,
            max_pings
            ):
    '''
    Точка входа модели Ping-Pong.
    Задать параметры работы.
    '''
    print(f'Running {MODEL_NAME} model')
    run_model(Config(
        interval=interval,
        channel_delay=channel_delay,
        service_delay=service_delay,
        loss_prob=loss_prob,
        max_pings=1_000_000
    ), ModelLoggerConfig())


def run_model(
    config: Config,
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
    # assert isinstance(result, Result)
    return result


if __name__ == '__main__':
    cli_run()
