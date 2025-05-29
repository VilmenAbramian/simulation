from typing import Optional, Sequence, Tuple

import numpy as np

from pysim.models.rfid import channel
from pysim.models.rfid.params import (
    default_params, inner_params
)


WAVELEN = inner_params.geometry_params.speed_of_light / inner_params.channel_params.frequency_hz
READER_POS = np.array((5, 0, 5))
READER_POLARIZATION = inner_params.channel_params.circular_polarization
TAG_POLARIZATION = inner_params.channel_params.horizontal_polarization


def get_pathloss(y, pol, speed, t):
    return channel.pathloss_model(
        time=t,
        wavelen=WAVELEN,
        # Параметры считывателя: ---------------------------
        tx_pos=np.array((READER_POS[0], y, READER_POS[2])), # Координата y изменяется
        tx_antenna_dir=inner_params.geometry_params.reader_antenna_direction,
        tx_rp=channel.rp_dipole,
        tx_velocity=np.array((0, channel.kmph2mps(speed), 0)), # Движение только по оси OY
        # Параметры метки: ---------------------------------
        rx_pos=np.array((5.0, 0, 0)),
        rx_antenna_dir=inner_params.geometry_params.tag_antenna_direction,
        rx_rp=channel.rp_dipole,
        rx_velocity=np.zeros(inner_params.geometry_params.dimension_of_space),
        # Параметры отражения: -----------------------------
        tx_polarization=pol,
        ground_reflection=channel.reflection,
        conductivity=inner_params.channel_params.conductivity,
        permittivity=inner_params.channel_params.permittivity,
        # ---------------------------------------------------
        log=True
    )


def get_tag_rx(y: float, speed: float, t: float, power: float = default_params.power_dbm) -> float:
    """
    Вычислить мощность сигнала, принятого меткой (в dBm).

    Скорость должна быть в км/ч
    """
    path_loss = get_pathloss(y, READER_POLARIZATION, speed, t)
    pol_loss = 0 if READER_POLARIZATION == TAG_POLARIZATION else -3.0
    gain = inner_params.energy_params.reader_antenna_gain + inner_params.energy_params.tag_antenna_gain
    return power + path_loss + pol_loss + gain + inner_params.energy_params.reader_cable_loss


def find_zones(
        x: Sequence[float], y: Sequence[float],
        bound: float, use_upper: bool = True
) -> Sequence[Tuple[float, float]]:
    """
    Найти интервалы на X, внутри которых значение Y выше или ниже лимита.

    Например, если use_upper = True, то есть ищем интервалы выше лимита, то
    возвращает набор интервалов `[(x0, x1), (x2, x3), ...]`, таких, что:
    - для x[2n] <= x <= x[2n+1]: y(x) >= B
    - для x[2n+1] <= x <= x[2n+2]: y(x) <= B

    Размерности x и y должны совпадать.

    Args:
        x (sequence of float): последовательность аргументов
        y (sequence of float): последовательность значений
        bound (float): граничное значение
        use_upper (bool): если True, то ищем области, в которых значение выше

    Returns:
        intervals (sequence of tuples): последовательность интервалов
    """
    # Специально делаем так, чтобы изначально is_upper не совпадало с тем,
    # что будет в первой точке:
    is_upper = False
    x_left: Optional[float] = None
    intervals = []

    for i, (xi, yi) in enumerate(zip(x, y)):

        is_start_point = False
        is_end_point = False

        if (not is_upper or (use_upper and i == 0)) and yi >= bound:

            # Если выполняется равенство, нужно проверить, возрастает
            # ли функция в этой точке. Если нет - игнорируем.
            if yi > bound or i == len(x) - 1 or y[i + 1] >= bound:
                is_upper = True
                if use_upper:
                    is_start_point = True
                else:
                    is_end_point = True

        elif (is_upper or (not use_upper and i == 0)) and yi <= bound:

            # Если выполняется равенство, нужно проверить, убывает
            # ли функция в этой точке. Если нет - игнорируем.
            if yi < bound or i == len(y) - 1 or y[i + 1] <= bound:
                is_upper = False
                if use_upper:
                    is_end_point = True
                else:
                    is_start_point = True

        if is_start_point:
            x_left = xi
        if is_end_point:
            intervals.append((x_left, xi))
            x_left = None

    # После цикла проверяем, не надо ли закрыть интервал.
    if x_left is not None:
        intervals.append((x_left, x[-1]))

    return intervals