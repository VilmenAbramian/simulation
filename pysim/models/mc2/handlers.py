import statistics
from pysim.sim import Simulator
from .objects import Config, Result
from .model import Model


def initialize(sim: Simulator, config: Config):
    # Init context
    model = Model(config=config, logger=sim.logger)
    sim.context = model
    # Schedle the first event
    sim.call(model.arbitrate.handle_timeout)


def finalize(sim: Simulator) -> Result:
    assert isinstance(sim.context, Model)
    # noinspection PyTypeChecker
    model: Model = sim.context
    print('Симуляция завершена')
