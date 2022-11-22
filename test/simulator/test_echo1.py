from datetime import datetime

import pytest

from pysim.sim import simulate, Simulator, ExitReason


# ============================================================================
# МОДЕЛЬ
# ============================================================================
def initialize(
        sim: Simulator,
        interval: float,
        max_served: int,
        stop_message: str
):
    sim.context = {
        # Config
        'interval': interval,
        'max_served': max_served,
        'stop_message': stop_message,
        # State
        'num_served': 0,
        'next_number': 100,
    }
    sim.schedule(interval, handle_timeout)


def handle_timeout(sim: Simulator):
    sim.call(handle_echo, args=(sim.context['next_number']))


def handle_echo(sim: Simulator, number: int):
    ctx: dict = sim.context
    ctx['num_served'] += 1
    ctx['next_number'] = number + 1
    if ctx['num_served'] >= ctx['max_served'] > 0:
        sim.stop(ctx['stop_message'])
    else:
        sim.schedule(ctx['interval'], handle_timeout, args=())


def finalize(sim: Simulator) -> dict:
    num_served = sim.context['num_served']
    max_served = sim.context['max_served']
    return {
        'total_served': num_served,
        'rest': max_served - num_served if max_served > 0 else None
    }


# ============================================================================
# ТЕСТЫ
# ============================================================================
# noinspection PyPep8Naming
def test_simulate_till_max():
    MAX_SERVED: int = 1000
    INTERVAL: float = 1.3

    t_start = datetime.now()
    stats, ctx, fin_ret = simulate(
        "Echo1",
        init=initialize,
        init_args=(INTERVAL, MAX_SERVED, "foobar"),
        fin=finalize,
        max_real_time=10.0,  # 10 секунд - это очень много
    )
    elapsed = datetime.now() - t_start

    # Проверяем статистику
    assert pytest.approx(elapsed, rel=0.1) == stats.time_elapsed
    assert MAX_SERVED * 2 == stats.num_events_processed
    assert pytest.approx(INTERVAL * MAX_SERVED, rel=0.01) == stats.sim_time
    assert ExitReason.STOPPED == stats.exit_reason
    assert "foobar" == stats.stop_message
    assert (handle_echo, (1 + MAX_SERVED,)) == stats.last_handler

    # Проверяем результаты
    # TODO
