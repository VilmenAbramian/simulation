from typing import Optional, Sequence, Tuple

import numpy as np

from pysim.models.rfid import channel
from pysim.models.rfid.params import (
    default_params, inner_params
)
import pysim.models.rfid.epcstd as epc


READER_POS = np.array((default_params.reader_offset, 0, default_params.altitude))
TAG_POS = np.array((default_params.tag_offset, 0, inner_params.tag_params.tag_altitude))

def get_noise(reader_noise, thermal_noise):
    return channel.to_log(
        value=(channel.from_log(reader_noise, dbm=True) + channel.from_log(thermal_noise, dbm=True)),
        dbm=True
    )


def get_pathloss(
    y: float, pol: float, speed: float = default_params.speed, t: float = 0.1
) -> float:
    """
    Расчёт затухания в двухлучевом канале (с отражением от стены).
    Значения затухания будут разными для каналов от считывателя к метке
    и обратно только из-за поляризации, так как от нее зависит
    коэффициент отражения. Все остальное - симметрично.

    Args:
        y: координата считывателя вдоль оси OY
        pol: поляризация сигнала (принимает значения: 0, 0.5, 1)
        speed: скорость считывателя вдоль оси OY, км/ч
        t: время с момента начала передачи

    Returns:
        затухание в dB
    """
    return channel.pathloss_model(
        time=t,
        wavelen=(inner_params.geometry_params.speed_of_light /
                 inner_params.channel_params.frequency_hz),
        # Параметры считывателя: ---------------------------
        tx_pos=np.array((READER_POS[0], y, READER_POS[2])), # Координата y изменяется
        tx_antenna_dir=inner_params.geometry_params.reader_antenna_direction,
        tx_rp=channel.rp_dipole,
        tx_velocity=np.array((0, channel.kmph2mps(speed), 0)), # Движение только по оси OY
        # Параметры метки: ---------------------------------
        rx_pos=TAG_POS,
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


def get_tag_rx(
        y: float,
        speed: float,
        t: float,
        reader_pol: float = inner_params.channel_params.reader_default_polarization,
        tag_pol:float = inner_params.channel_params.tag_default_polarization,
        power: float = default_params.power_dbm
) -> float:
    """
    Вычислить мощность сигнала, принятого меткой (в dBm).

    Скорость должна быть в км/ч

    Args:
        y: положение считывателя по оси OY;
        speed: скорость считывателя, км/ч
        t: время, сек;
        reader_pol: поляризация антенны считывателя;
        tag_pol: поляризация антенны метки;
        power: мощность передатчика считывателя.
    """
    path_loss = get_pathloss(y, reader_pol, speed, t)
    pol_loss = (
        0 if reader_pol==tag_pol else inner_params.energy_params.polarization_loss
    )
    gain = (inner_params.energy_params.reader_antenna_gain +
            inner_params.energy_params.tag_antenna_gain)
    return (power + path_loss + pol_loss + gain +
            inner_params.energy_params.reader_cable_loss)


def get_tag_tx(
        power: float,
        tag_backscatter_loss = inner_params.energy_params.tag_modulation_loss
) -> float:
    """Вычислить мощность сигнала, отраженного меткой (в dBm)."""
    return power + tag_backscatter_loss


def get_reader_rx(
        y: float,
        speed: float,
        t: float,
        power: float,
        tag_pol = inner_params.channel_params.tag_default_polarization,
        reader_pol = inner_params.channel_params.reader_default_polarization,
        reader_gain = inner_params.energy_params.reader_antenna_gain,
        tag_gain = inner_params.energy_params.tag_antenna_gain ,
        reader_cable_loss = inner_params.energy_params.reader_cable_loss
) -> float:
    """
    Вычислить мощность сигнала, принятого считывателем (в dBm).

    Скорость должна быть в км/ч
    """
    path_loss = get_pathloss(y, tag_pol, speed, t)
    pol_loss = 0 if reader_pol == tag_pol else inner_params.energy_params.polarization_loss
    gain = reader_gain + tag_gain
    return power + path_loss + pol_loss + gain + reader_cable_loss


def get_snr(
        rx: float,
        m: int,
        trcal: float,
        reader_noise:float = inner_params.energy_params.reader_noise,
        thermal_noise: float = inner_params.energy_params.thermal_noise,
        trext: bool = False,
        dr: epc.DivideRatio = inner_params.tag_params.dr,
) -> float:
    """Вычислить SNR на бит с поправкой на синхронизацию."""
    snr = channel.snr(power=rx, noise=get_noise(reader_noise, thermal_noise))
    preamble = epc.get_preamble(m, trcal, trext, dr)
    return channel.snr_full(
        snr=snr,
        miller=m,
        symbol=(1 / epc.get_blf(dr, trcal)),
        preamble=preamble
    )


def find_zones(
        x: Sequence[float],
        y: Sequence[float],
        bound: float = inner_params.energy_params.tag_sensitivity,
        use_upper: bool = True
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
        bound (float): граничное значение (чувствительность метки)
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