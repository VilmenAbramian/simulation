import click

from pysim.sim import simulate, ModelLoggerConfig
from .config import Config
from .result import Result
from .handlers import initialize, finalize

MODEL_NAME = "PingPongOOP"

@click.command()
# Common
@click.option("--max-sim-time", type=float, help="Max simulation time")
@click.option("--max-real-time", type=float, help="Max real time elapsed")
@click.option("--max-num-events", type=int, help="Max number of events")
@click.option(
    "--use-log-file", type=str, help=f"Record log to file {MODEL_NAME}.log"
)
@click.option(
    "--log-runid/--no-log-runid", type=bool, default=False,
    help="Show "
)
# Semi-common
@click.option("--json")
@click.argument()
# Custom
@click.option("--max-sim-time", type=float, help="Max simulation time")
def cli_run():
    print("Running echo model")


def run_model(
    config: Config, 
    logger_config: ModelLoggerConfig,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None,
) -> Result:
    sim_time, _, result = simulate(
        MODEL_NAME,
        init=initialize,
        init_args=(config,),
        fin=finalize,
        max_real_time=max_real_time,
        max_sim_time=max_sim_time,
        max_num_events=max_num_events,
        logger_config=logger_config
    )
    assert isinstance(result, Result)
    return result
