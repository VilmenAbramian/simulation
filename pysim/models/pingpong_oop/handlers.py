import statistics
from pysim.sim import Simulator
from .objects import Config, Result
from .model import Model


def initialize(sim: Simulator, config: Config):
    # Init context
    model = Model(config=config, logger=sim.logger)
    sim.context = model
    # Schedle the first event
    sim.call(model.client.handle_timeout)


def finalize(sim: Simulator) -> Result:
    assert isinstance(sim.context, Model)
    # noinspection PyTypeChecker
    model: Model = sim.context

    return Result(
        avg_interval=statistics.mean(model.client.intervals_list),
        avg_delay=statistics.mean(model.channel.delays_list),
        miss_rate=(
            model.client.num_acknowledged / model.client.num_pings_sent
        ),
    )
