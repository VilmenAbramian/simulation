from numpy import linalg as la
from numpy.typing import NDArray
from typing import Callable

import numpy as np
import scipy
import scipy.special as special

# --------------------------------------------
# Вспомогательные функции. Перевод величин
# --------------------------------------------
def to_sin(cos):
    return (1 - cos ** 2) ** .5


def to_log(value, dbm=False, tol=1e-15):
    return 10 * np.log10(value) + 30 * int(dbm) if value >= tol else -np.inf


def from_log(value, dbm=False):
    return 10 ** (value / 10 - 3 * int(dbm))


def vec3D(x, y, z):
    return np.array([x, y, z])


def to_power(value, log=True, dbm=False):
    power = np.abs(value) ** 2
    return to_log(power, dbm=dbm) if log else power


def deg2rad(angle: float) -> float:
    """Перевести угол из градусов в радианы."""
    return angle / 180.0 * np.pi


def lin2db(value_linear):
    """Перевести линейное отношение в дБ."""
    return 10 * np.log10(value_linear) if value_linear >= 1e-15 else -np.inf


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
def two_ray_pathloss(
        time:float,
        ground_reflection:Callable,
        wavelen:float,
        tx_pos:NDArray[float],
        tx_dir_theta:NDArray[float],
        tx_velocity:NDArray[float],
        tx_rp:Callable,
        rx_pos:NDArray[float],
        rx_dir_theta:NDArray[float],
        rx_velocity:NDArray[float],
        rx_rp:Callable,
        log=True,
        **kwargs
):
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

    Args:
        time: время, прошедшее с начала приема
        ground_reflection: функция для вычисления комплексного коэффициента отражения
        wavelen: длина волны
        tx_pos: текущее положение передатчика
        tx_dir_theta: вектор направления главного луча антенны передатчика
        tx_velocity: скорость передатчика
        tx_rp: диаграмма направленности передатчика
        rx_pos: текущее положение приёмника
        rx_dir_theta: вектор направления главного луча антенны приёмника
        rx_velocity: скорость приёмника
        rx_rp: диаграмма направленности приёмника
    Return:
        Затухание в двухлучевом канале
    '''
    # Вычисление геометрии прямого и отражённого от стены лучей
    wall_normal = np.array([1, 0, 0]) # Нормаль к стене, от которой происходит отражение
    rx_pos_refl = np.array([-rx_pos[0], rx_pos[1], rx_pos[2]]) # 'Зазеркальный'приёмник

    d0_vector = rx_pos - tx_pos  # LoS
    d1_vector = rx_pos_refl - tx_pos  # NLoS
    d0 = np.linalg.norm(d0_vector)  # Длина LoS
    d1 = np.linalg.norm(d1_vector)  # Длина NLoS

    d0_vector_tx_n = d0_vector / d0  # LoS нормализован
    d0_vector_rx_n = -d0_vector_tx_n # Минус для того, чтобы скалярное произведение было положительным
    d1_vector_tx_n = d1_vector / d1  # NLoS нормализован
    d1_vector_rx_n = np.array([-d1_vector_tx_n[0], d1_vector_tx_n[1], d1_vector_tx_n[2]])

    # theta - семейство углов между направлениями главных лучей антенн
    # приёмника/передатчика и направлениями LoS/NLoS
    tx_azimuth_0 = np.dot(d0_vector_tx_n, tx_dir_theta) # Косинус между антенной передатчика и LoS
    rx_azimuth_0 = np.dot(d0_vector_rx_n, rx_dir_theta) # Косинус между антенной приёмника и LoS
    tx_azimuth_1 = np.dot(d1_vector_tx_n, tx_dir_theta) # Косинус между антенной передатчика и NLoS
    rx_azimuth_1 = -1 * np.dot(d1_vector_rx_n, rx_dir_theta) # Косинус между антенной приёмника и NLoS

    # A grazing angle of NLoS ray for computation of reflection coefficient
    grazing_angle = -1 * np.dot(d1_vector_rx_n, wall_normal)  # Версия Андрея

    relative_velocity = rx_velocity - tx_velocity
    velocity_pr_0 = np.dot(d0_vector_tx_n, relative_velocity)
    velocity_pr_1 = np.dot(d1_vector_tx_n, relative_velocity)

    # Затухание, определяемое ДН передающей и принимающей антенн
    g0 = (tx_rp(azimuth=tx_azimuth_0) * rx_rp(azimuth=rx_azimuth_0))
    g1 = (tx_rp(azimuth=tx_azimuth_1) * rx_rp(azimuth=rx_azimuth_1))

    # Затухание, вызванное отражением сигнала
    r0 = 1 # прямой луч ни от чего не отражается
    r1 = ground_reflection(cosine=grazing_angle, wavelen=wavelen, **kwargs)

    k = 2 * np.pi / wavelen # волновое число

    return (0.5 / k) ** 2 * np.absolute(r0 * g0 / d0 * np.exp(-1j * k * (d0 - time * velocity_pr_0)) +
                                        r1 * g1 / d1 * np.exp(-1j * k * (d1 - time * velocity_pr_1))) ** 2


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

# ----------------------------------------------------------------------------
# Накидывание говна
# ----------------------------------------------------------------------------

# Функция, рассчитывающая потери в свободном пространстве
def free_space_path_loss_3d(
        *, time, wavelen,
        tx_pos, tx_dir_theta, tx_velocity, tx_rp,
        rx_pos, rx_dir_theta, rx_velocity, rx_rp,
        **kwargs):
    """
    Computes free space signal attenuation between the transmitter and the
    receiver in linear scale.
    :param wavelen: a wavelen of signal carrier
    :param time: Time passed from the start of reception (это константа!)
    :param tx_velocity: the velocity of the transmitter
    :param tx_dir_theta: the vector pointed the direction with azimuth
        angle equals 0 of the transmitter antenna.
    :param tx_pos: a current position of the transmitter.
    :param tx_rp: a radiation pattern of the transmitter
    :param rx_velocity: the velocity of the receiver
    :param rx_dir_theta: the vector pointed the direction with azimuth angle
        equals 0 of the transmitter antenna.
    :param rx_pos: a current position of the receiver
    :param rx_rp: a radiation pattern of the receiver
    :return: free space path loss in linear scale
    """
    d_vector = rx_pos - tx_pos
    d = la.norm(d_vector)
    d_vector_tx_n = d_vector / d
    d_vector_rx_n = -d_vector_tx_n

    # Azimuth angle computation for computation of attenuation
    # caused by deflection from polar direction
    tx_azimuth = np.dot(d_vector_tx_n, tx_dir_theta)
    rx_azimuth = np.dot(d_vector_rx_n, rx_dir_theta)

    relative_velocity = rx_velocity - tx_velocity
    velocity_pr = np.dot(d_vector_tx_n, relative_velocity)

    # Attenuation caused by radiation pattern
    g0 = tx_rp(azimuth=tx_azimuth) * rx_rp(azimuth=rx_azimuth)

    k = 2 * np.pi / wavelen
    return (0.5/k)**2 * np.abs(g0/d*np.exp(-1j*k*(d - time * velocity_pr)))**2
