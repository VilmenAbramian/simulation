import click
from multiprocessing import Pool
import multiprocessing

from pysim.sim.simulator import (
    build_simulation,
    run_simulation,
    ModelLoggerConfig
)
from objects import Config, Result
from pysim.models.pingpong_oop.handlers import initialize, finalize

MODEL_NAME = 'PingPongOOP'
DEFAULT_INTERVAL = 10.0
DEFAULT_LOSS_PROB = 0.1
DEFAULT_CHANNEL_DELAY = 2.0
DEFAULT_SERVICE_DELAY = 1.0
MAX_PINGS = 1000000


def check_vars_for_multiprocessing(**kwargs):
    '''
    Проверка, указан ли какой-то параметр несколько раз.
    Если такой есть и он один, то выполним несколько симуляций параллельно.
    Если все параметры даны в одном экземпляре, то выполним одну симуляцию.
    Если несколько параметров заданы со множеством значений, это ошибка.
    '''
    var_arg_names = ('interval', 'channel_delay', 'service_delay',
                     'loss_prob', 'max_pings')
    variadic = None
    for arg_name in var_arg_names:
        if len(kwargs[arg_name]) > 1:
            if variadic is not None:
                print("Error: only one argument can have multiple values, "
                      f"not both \"{variadic}\" and \"{arg_name}\"")
                return -1
            variadic = arg_name
        else:
            kwargs[arg_name] = kwargs[arg_name][0]
    return kwargs, variadic


def run_multiple_simulation(variadic, **kwargs):
    '''
    Какой-то параметр варьируется. Запускаем параллельно расчеты через
    пул рабочих.
    Убираем дубликаты и сортируем по возрастанию значения аргумента,
    по которому варьируемся.
    '''
    variadic_values = sorted(set(kwargs[variadic]))

    # Построим массив из копий параметров
    args_list = [{
        'interval': kwargs['interval'],
        'channel_delay': kwargs['channel_delay'],
        'service_delay': kwargs['service_delay'],
        'loss_prob': kwargs['loss_prob'],
        'max_pings': kwargs['max_pings'],
    } for _ in enumerate(variadic_values)]

    # Теперь заменим значения варьируемого аргумента, чтобы в каждом
    # элементе args хранилось только одно значение вместо всего набора.
    for i, value in enumerate(variadic_values):
        args_list[i][variadic] = value

    pool = Pool(kwargs.get('jobs', multiprocessing.cpu_count()))
    return pool.map(create_config, args_list)


@click.command()
@click.option(
    '-i', '--interval', default=(DEFAULT_INTERVAL, ), multiple=True,
    help='Интервал отправки Ping клиентом (условные единицы)',
    show_default=True
)
@click.option(
    '-ch', '--channel_delay', default=(DEFAULT_CHANNEL_DELAY, ), multiple=True,
    help='Длительность передачи сообщения (условные единицы)',
    show_default=True
)
@click.option(
    '-s', '--service_delay', default=(DEFAULT_SERVICE_DELAY, ), multiple=True,
    help='Длительность обслуживания Ping',
    show_default=True
)
@click.option(
    '-l', '--loss_prob', default=(DEFAULT_LOSS_PROB, ), multiple=True,
    help='Вероятность потери пакета в канале',
    show_default=True
)
@click.option(
    '-mp', '--max_pings', default=(MAX_PINGS, ), multiple=True,
    help='Количество отправляемых клиентом Ping-ов',
    show_default=True
)
def cli_run(**kwargs):
    '''
    Точка входа модели Ping-Pong.
    Задать параметры работы.
    '''
    kwargs, variadic = check_vars_for_multiprocessing(**kwargs)
    print(f'Running {MODEL_NAME} model')
    if variadic is None:
        result = create_config(kwargs)
        print(result)
    else:
        result = run_multiple_simulation(variadic, **kwargs)
        print(result[0].avg_delay)


def create_config(*args):
    kwargs = args[0]
    return run_model(Config(
        interval=kwargs['interval'],
        channel_delay=kwargs['channel_delay'],
        service_delay=kwargs['service_delay'],
        loss_prob=kwargs['loss_prob'],
        max_pings=kwargs['max_pings']
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
    return result


if __name__ == '__main__':
    cli_run()
