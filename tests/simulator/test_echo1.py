from datetime import datetime

import pytest

from pysim.sim import build_simulation, run_simulation, Simulator, ExitReason


# ============================================================================
# Модель Echo-1
# -------------
#
# Модель имитирует появление заявок через равные промежутки времени.
#
# Каждая заявка характеризуется одним числом (его номером), стартовый номер
# может быть произвольным.
#
# В модели есть два события:
# 1. Таймаут - появление новой заявки, вызывает начало обслуживания.
# 2. Обслуживание - имитация мгновенного обслуживания, просто увеличивает
#       число обслуженных пакетов и планирует приход следующей заявки. Если
#       сгенерировано достаточно заявок, остановить симуляцию.
#
# При обработке таймаута начало обслуживания вызывается как отдельное событие,
# через simulator.call().
#
# Результат модели:
# - число обработанных заявок
# - число необработанных заявок (сколько осталось до max_served)
# ============================================================================
def initialize(
        sim: Simulator,
        interval: float,
        max_served: int,
        stop_message: str
):
    sim.context = {
        # НАСТРОЙКИ МОДЕЛИ
        'interval': interval,           # интервал между заявками
        'max_served': max_served,       # макс. число обслуженных заявок
        'stop_message': stop_message,   # сообщение для вывода в конце
        # СОСТОЯНИЕ МОДЕЛИ
        'num_served': 0,                # сколько заявок было обслужено
        'next_number': 100,             # число в следующей заявке
    }
    sim.schedule(interval, handle_timeout)


def handle_timeout(sim: Simulator):
    sim.call(handle_service, args=(sim.context['next_number'],))


def handle_service(sim: Simulator, number: int):
    ctx: dict = sim.context
    ctx['num_served'] += 1
    ctx['next_number'] = number + 1
    if (ctx['max_served'] is not None and
            ctx['num_served'] >= ctx['max_served'] > 0):
        sim.stop(ctx['stop_message'])
    else:
        sim.schedule(ctx['interval'], handle_timeout, args=())


def finalize(sim: Simulator) -> dict:
    num_served = sim.context['num_served']
    max_served = sim.context['max_served']

    return {
        'total_served': num_served,
        'rest': max_served - num_served if (max_served != None and max_served > 0) else None
    }


# ============================================================================
# ТЕСТЫ
# ============================================================================
# noinspection PyPep8Naming
def test_simulate_till_max():
    """
    Выполняем симуляцию до достижения числа обслуженных заявок, указанного
    в конфигурации (max_served). Проверяем, что:

    1) Число обработанных событий = 2 * число заявок
    2) Модельное время = число заявок * интервал
    3) Реальное время было записано корректно
    4) Причина остановки = STOPPED
    5) Последним обработчиком был handle_service()
    6) Выдача правильного сообщения при остановке
    7) Статистика правильно подсчитана:
       - число обслуженных заявок = max_served
       - число необслуженных заявок = 0
    8) Вторая компонента результата - контекст
    """
    MAX_SERVED: int = 1000
    INTERVAL: float = 1.3
    stop_message = "foobar"

    t_start = datetime.now()

    # Вызов simulate() возвращает статистику, контекст, результаты

    sim = build_simulation(
        "Echo1",
        init=initialize,
        init_args=(INTERVAL, MAX_SERVED, stop_message),
        fin=finalize,
        max_real_time=10.0,  # 10 секунд - это очень много
    )

    stats, ctx, fin_ret = next(sim)
    elapsed = datetime.now() - t_start

    with pytest.raises(StopIteration):
        next(sim)

    # Проверяем статистику
    assert elapsed.seconds < 2.0  # не более 2 секунд, реально должно быть еще меньше
    assert pytest.approx(elapsed.microseconds, rel=1) == int(stats.time_elapsed * 10 ** 6)
    assert MAX_SERVED * 2 == stats.num_events_processed
    assert pytest.approx(INTERVAL * MAX_SERVED, rel=0.01) == stats.sim_time
    assert ExitReason.STOPPED == stats.exit_reason
    assert stop_message == stats.stop_message
    assert handle_service == stats.last_handler

    # Проверяем результаты
    assert MAX_SERVED == fin_ret.get("total_served")
    assert 0 == fin_ret.get("rest")

    # Проверяем наличие контекста
    assert {"interval", "max_served", "stop_message", "num_served",
            "next_number"} == set(ctx.keys())


def test_simulate_till_sim_time():
    """
    Выполняем симуляцию до достижения предельного модельного времени T,
    за которое будет обработано N заявок, N < N_MAX.

    Проверяем, что:

    1) Число обработанных событий = 2*N
    2) Модельное время не превышает T более, чем на Ai (интервал генерации)
    3) Число обработанных заявок = N
    4) Число необработанных заявок = N_MAX - N
    5) Причина остановки - вызов stop()
    """
    max_served: int = 1000
    interval: float = 2.6
    max_sim_time = 500.0
    expected_num_served = 192  # 500 / 2.6 = 192.3
    stop_message = "foobar"

    stats, ctx, fin_ret = run_simulation(
        build_simulation(
            "Echo1",
            init=initialize,
            init_args=(interval, max_served, stop_message),
            fin=finalize,
            max_real_time=10.0,
            max_sim_time=max_sim_time,
        ))

    eps = ctx["interval"] * 0.01
    # Погрешность, обусловленная возможностью заявки заскочить в "последний" вагон (до неё время - 499, после неё - 501)
    eps_event = 2
    assert stats.num_events_processed / 2 - eps_event <= expected_num_served <= stats.num_events_processed / 2 + eps_event
    assert (max_sim_time + eps < stats.sim_time <=
            max_sim_time + ctx["interval"] + eps)
    assert expected_num_served == fin_ret['total_served']
    assert max_served - expected_num_served == fin_ret['rest']
    assert ExitReason.REACHED_SIM_TIME_LIMIT == stats.exit_reason


def test_simulate_till_real_time():
    """
    Выполняем симуляцию до истечения предельного реального времени.

    Проверяем, что реальное время близко к ожидаемому значению и причину
    остановки. Больше ничего конкретного про модель сказать не можем.
    """
    max_real_time = 1.0
    eps = 0.05

    stats, _, _ = run_simulation(
        build_simulation(
            "Echo1",
            init=initialize,
            init_args=(10.0, None, "bazzzz"),
            fin=finalize,
            max_real_time=max_real_time,
            max_sim_time=None,
        ))

    assert ExitReason.REACHED_REAL_TIME_LIMIT == stats.exit_reason
    assert max_real_time - eps <= stats.time_elapsed <= max_real_time + eps


# def test_simulate_steps_in_debug():
#     """
#     Выполняем первые несколько шагов в режиме отладки.
#     """
#     max_served: int = 1000
#     interval: float = 2.0
#     max_sim_time = 9.0
#
#     sim = build_simulation(
#         "Echo1",
#         init=initialize,
#         init_args=(interval, max_served, "foobarbaz"),
#         fin=finalize,
#         max_real_time=None,
#         max_sim_time=max_sim_time,
#         debug=True
#     )
#
#     # 1) После первой итерации должны оказаться у обработчика таймаута
#     stats, ctx, fin_ret = next(sim)
#     assert stats.last_handler is None
#     assert stats.next_handler is handle_timeout
#     assert interval == stats.sim_time
#     assert 0 == stats.last_sim_time

    # 2) Делаем еще итерацию - то же время, но новый обработчик
    # TODO
