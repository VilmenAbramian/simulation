from pysim.sim import Simulator
from .objects import Config
from .model import Model


def initialize(sim: Simulator, config: Config):
    # Init context
    model = Model(config=config, logger=sim.logger)
    sim.context = model
    # Schedle the first event
    sim.call(model.arbitrate.handle_timeout)


def finalize(sim: Simulator):
    assert isinstance(sim.context, Model)
    print('Симуляция завершена')
