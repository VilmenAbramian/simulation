from numpy.typing import NDArray
from typing import Callable, Optional

import numpy as np
import scipy
import scipy.special as special

# --------------------------------------------
# Вспомогательные функции. Перевод величин
# --------------------------------------------
def to_sin(cos):
    return (1 - cos ** 2) ** .5


def to_log(value, dbm=False, tol=1e-15):
    """Перевести линейное отношение в дБ."""
    return 10 * np.log10(value) + 30 * int(dbm) if value >= tol else -np.inf


def from_log(value, dbm=False):
    return 10 ** (value / 10 - 3 * int(dbm))


def vec3D(x, y, z):
    return np.array([x, y, z])


def deg2rad(angle: float) -> float:
    """Перевести угол из градусов в радианы."""
    return angle / 180.0 * np.pi


def kmph2mps(speed: float) -> float:
    """Перевести км/ч в м/с."""
    return speed * 5 / 18

# --------------------------------------------
# Диаграмма направленности
# --------------------------------------------
def rp_dipole(*, azimuth, tol=1e-9):
    a_sin = to_sin(azimuth)
    return np.abs(np.cos(np.pi / 2 * a_sin) / azimuth) if azimuth > tol else 0.


# --------------------------------------------
# Коэффициент отражения
# --------------------------------------------
def __c_parallel(cosine, permittivity, conductivity, wavelen):
    eta = permittivity - 60j * wavelen * conductivity
    return (eta - cosine ** 2) ** 0.5


def __c_perpendicular(cosine, permittivity, conductivity, wavelen):
    eta = permittivity - 60j * wavelen * conductivity
    return (eta - cosine ** 2) ** 0.5 / eta


def reflection_constant(**kwargs):
    return -1.0 + 0.j


def reflection(
        cosine: float,
        polarization,
        permittivity,
        conductivity,
        wavelen,
        **kwargs
    ):
    '''
    Расчитать коэффициент отражения.

    Args:
        cosine: косинус угла падения
        pol (float): поляризация
        permittivity (float)
        conductivity (float)
        wavelen (float)
    '''
    sine = (1 - cosine ** 2) ** .5

    if polarization != 0:
        c_parallel = __c_parallel(cosine, permittivity, conductivity, wavelen)
        r_parallel = (sine - c_parallel) / (sine + c_parallel)
    else:
        r_parallel = 0.j

    if polarization != 1:
        c_perpendicular = __c_perpendicular(cosine, permittivity, conductivity, wavelen)
        r_perpendicular = (sine - c_perpendicular) / (sine + c_perpendicular)
    else:
        r_perpendicular = 0.j

    return polarization * r_parallel + (1 - polarization) * r_perpendicular


# --------------------------------------------
# Pathloss - потери в канале
# --------------------------------------------
def pathloss_model(
    time: float, wavelen: float,

    tx_pos: NDArray[np.float64],
    tx_antenna_dir: NDArray[np.float64],
    tx_rp: Callable,
    tx_velocity: NDArray[np.float64],

    rx_pos: NDArray[np.float64],
    rx_antenna_dir: NDArray[np.float64],
    rx_rp: Callable,
    rx_velocity: NDArray[np.float64],

    tx_polarization: float = None,
    ground_reflection: Optional[Callable] = None,
    conductivity: float = None,
    permittivity: float = None,
    log: bool = True,
) -> float:
    '''
    Вычисляет затухание сигнала в свободном пространстве между передатчиком и приемником в линейном масштабе.

    Так как отражённый луч состоит из двух частей: передатчик-стена + стена-приёмник, то для его
    анализа нужно рассматривать обе части. Но вместо этого можно представить этот составной луч
    как один, но такой же длины - как если бы он прошёл сквозь стену и попал на 'зазеркальную'
    метку. Координаты такой метки (если метка выступает в качестве приёмника):
    [-rx_pos[0], rx_pos[1], rx_pos[2]]. Минус перед координатой абцисс (X) как раз и
    означает, что метка в 'зазеркалье', так как 'зеркало'-стена находится в плоскости YOZ.
    Также данные лучи для краткости обозначаются как:
    LoS - Line-of-Sight, прямой луч;
    NLoS - Non-Line-of-Sight, отражённый луч
    3D модель с геометрическим смыслом переменных и логики данной функции можно найти в
    папке experiments.

    Args:
        time: время, прошедшее с начала приема
        wavelen: длина волны
        tx_pos: текущее положение передатчика
        tx_antenna_dir: вектор направления главного луча антенны передатчика
        tx_rp: диаграмма направленности передатчика
        tx_velocity: скорость передатчика
        rx_pos: текущее положение приёмника
        rx_antenna_dir: вектор направления главного луча антенны приёмника
        rx_rp: диаграмма направленности приёмника
        tx_polarization: поляризация антенны передатчика
        rx_velocity: скорость приёмника
        ground_reflection: функция для вычисления комплексного коэффициента отражения
        conductivity: проводимость поверхности отражения
        permittivity: диэлектрическая проницаемость поверхности отражения
        log: если True вернуть значение в дБ (логарифмический масштаб), если False вернуть в Вт (линейный масштаб)
    Return:
        Затухание в канале
    '''
    d_vector = rx_pos - tx_pos
    d = np.linalg.norm(d_vector)
    d_vector_tx_n = d_vector / d
    d_vector_rx_n = -d_vector_tx_n

    tx_azimuth = np.dot(d_vector_tx_n, tx_antenna_dir)
    rx_azimuth = np.dot(d_vector_rx_n, rx_antenna_dir)

    relative_velocity = rx_velocity - tx_velocity
    velocity_pr = np.dot(d_vector_tx_n, relative_velocity)

    k = 2 * np.pi / wavelen
    r0 = 1
    g0 = tx_rp(azimuth=tx_azimuth) * rx_rp(azimuth=rx_azimuth)
    phase_shift_0 = -1j * k * (d - time * velocity_pr)

    pathloss = (0.5 / k) ** 2 * np.abs(g0 / d * np.exp(phase_shift_0)) ** 2

    if ground_reflection is not None:
        wall_normal = np.array([1, 0, 0])  # Нормаль к стене, от которой происходит отражение
        rx_pos_refl = rx_pos.copy()
        rx_pos_refl[0] *= -1

        d1_vector = rx_pos_refl - tx_pos
        d1 = np.linalg.norm(d1_vector)
        d1_vector_tx_n = d1_vector / d1
        d1_vector_rx_n = np.array([-d1_vector_tx_n[0], d1_vector_tx_n[1], d1_vector_tx_n[2]])

        tx_azimuth_1 = np.dot(d1_vector_tx_n, tx_antenna_dir)
        rx_azimuth_1 = -1 * np.dot(d1_vector_rx_n, rx_antenna_dir)
        velocity_pr_1 = np.dot(d1_vector_tx_n, relative_velocity)

        g1 = tx_rp(azimuth=tx_azimuth_1) * rx_rp(azimuth=rx_azimuth_1)
        grazing_angle = -1 * np.dot(d1_vector_rx_n, wall_normal)
        r1 = ground_reflection(
            cosine=grazing_angle, wavelen=wavelen,
            conductivity=conductivity, permittivity=permittivity,
            polarization=tx_polarization
        )
        phase_shift_1 = -1j * k * (d1 - time * velocity_pr_1)

        pathloss = (0.5 / k) ** 2 * np.abs(r0 * g0 / d * np.exp(phase_shift_0) +
                                      r1 * g1 / d1 * np.exp(phase_shift_1)) ** 2

    return to_log(pathloss) if log else pathloss


#
# BER computation functions
#
def snr(power, noise):
    return from_log(power - noise)


def snr_full(*, snr, miller=1, symbol=1.25e-6, preamble=9.3e-6,
             bandwidth=1.2e6, tol=1e-8, **kwargs):
    if snr < tol:
        return 0.5

    # print(">>> miller={}, symbol={}, preamble={}, bandwidth={}".format(
    #     miller, symbol, preamble, bandwidth
    # ))
    # print('++++++++++', snr, preamble, bandwidth, miller, symbol)
    sync_angle = (snr * preamble * bandwidth) ** -0.5
    return miller * snr * symbol * bandwidth * np.cos(sync_angle) ** 2


def q_func(x):
    return 0.5 - 0.5 * scipy.special.erf(x / 2 ** 0.5)


def ber(snr, distr='rayleigh', tol=1e-8):
    if snr < tol:
        return 0.5
    if distr == 'rayleigh':
        t = (1 + 2 / snr) ** 0.5
        return 0.5 - 1 / t + 2 / np.pi * np.arctan(t) / t
    else:
        t = q_func(snr ** 0.5)
        return 2 * t * (1 - t)
