import click

from pysim.sim.simulator import build_simulation, run_simulation, ModelLoggerConfig
from config import Config
from result import Result
from pysim.models.pingpong_oop.handlers import initialize, finalize

MODEL_NAME = "PingPongOOP"


@click.command()
def cli_run():
    print(f"Running {MODEL_NAME} model")
    run_model(Config(
        interval=10.0,
        channel_delay=2.0,
        service_delay=1.0,
        loss_prob=0.1,
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