import numpy as np
from numpy import linalg as la
import scipy
import scipy.special as special


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


#
# Radiation Pattern
#
def __patch_factor(a_cos, t_cos, wavelen, width, length, tol=1e-9):
    a_sin = to_sin(a_cos)
    t_sin = to_sin(t_cos)
    kw = np.pi / wavelen * width
    kl = np.pi / wavelen * length
    if a_cos < tol:
        return 0
    if np.abs(a_sin) < tol:
        return 1.
    elif np.abs(t_sin) < tol:
        return np.cos(kl * a_sin)
    else:
        return np.sin(kw * a_sin * t_sin) / (kw * a_sin * t_sin) * np.cos(kl * a_sin * t_cos)


def __patch_theta(a_cos, t_cos, wavelen, width, length):
    return __patch_factor(a_cos, t_cos, wavelen, width, length) * t_cos


def __patch_phi(a_cos, t_cos, wavelen, width, length):
    return -1 * __patch_factor(a_cos, t_cos, wavelen, width, length) * to_sin(t_cos) * a_cos


def rp_isotropic(**kwargs):
    return 1.0


def rp_dipole(*, azimuth, tol=1e-9):
    a_sin = to_sin(azimuth)
    return np.abs(np.cos(np.pi / 2 * a_sin) / azimuth) if azimuth > tol else 0.


def rp_patch(*, a_cos, t_cos, wavelen, width, length):
    return (np.abs(__patch_factor(a_cos, t_cos, wavelen, width, length)) *
            (t_cos ** 2 + a_cos ** 2 * to_sin(t_cos) ** 2) ** 0.5)


#
# Reflection
#
def __c_parallel(cosine, permittivity, conductivity, wavelen):
    eta = permittivity - 60j * wavelen * conductivity
    return (eta - cosine ** 2) ** 0.5


def __c_perpendicular(cosine, permittivity, conductivity, wavelen):
    eta = permittivity - 60j * wavelen * conductivity
    return (eta - cosine ** 2) ** 0.5 / eta


def reflection_constant(**kwargs):
    return -1.0 + 0.j


def reflection(*, cosine, polarization, permittivity, conductivity, wavelen, **kwargs):
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


#
# Pathloss
#
def two_ray_pathloss(*, time, ground_reflection, wavelen,
                     tx_pos, tx_dir_theta, tx_dir_phi, tx_velocity, tx_rp,
                     rx_pos, rx_dir_theta, rx_dir_phi, rx_velocity, rx_rp, log=False, crutch=False, **kwargs):
    """
    Computes free space signal attenuation between the transmitter and the receiver in linear scale.
    :param wavelen: a wavelen of signal carrier
    :param time: Time passed from the start of reception
    :param ground_reflection: a function to compute a complex-valued reflection coefficient
    :param tx_velocity: the velocity of the transmitter
    :param tx_dir_theta: the vector pointed the direction with azimuth angle equals 0 of the transmitter antenna.
    :param tx_pos: a current position of the transmitter.
    :param tx_rp: a radiation pattern of the transmitter
    :param rx_velocity: the velocity of the receiver
    :param rx_dir_theta: the vector pointed the direction with azimuth angle equals 0 of the transmitter antenna.
    :param rx_pos: a current position of the receiver
    :param rx_rp: a radiation pattern of the receiver
    :return: free space path loss in linear scale
    """
    # LoS - Line-of-Sight, NLoS - Non-Line-of-Sight

    # Ray geometry computation
    # print(f"tx-pos: {tx_pos}, rx-pos: {rx_pos}")
    ground_normal = np.array([1, 0, 0])
    rx_pos_refl = np.array([-rx_pos[0], rx_pos[1], rx_pos[2]])  # Reflect RX relatively the ground. Координаты метки "под землёй". Это "тень" метки, благодаря которой мы можем узнать координаты точки отражения (точка математически условна, так как находится под землёй)

    d0_vector = rx_pos - tx_pos  # LoS ray vector
    d1_vector = rx_pos_refl - tx_pos  # NLoS ray vector
    d0 = la.norm(d0_vector)  # LoS ray length
    d1 = la.norm(d1_vector)  # NLoS ray length
    d0_vector_tx_n = d0_vector / d0  # LoS ray vector normalized
    d0_vector_rx_n = -d0_vector_tx_n
    d1_vector_tx_n = d1_vector / d1  # NLoS ray vector normalized
    d1_vector_rx_n = np.array([-d1_vector_tx_n[0], -d1_vector_tx_n[1], d1_vector_tx_n[2]])

    # Предполагается, что стена, от которой происходит отражение - это плоскость YOZ
    x_rfp = 0
    y_rfp = -tx_pos[0] * (rx_pos_refl[1] - tx_pos[1]) / (rx_pos_refl[0] - tx_pos[0]) + tx_pos[1]
    z_rfp = -tx_pos[0] * (rx_pos_refl[2] - tx_pos[2]) / (rx_pos_refl[0] - tx_pos[0]) + tx_pos[2]
    ref_point = np.array([x_rfp, y_rfp, z_rfp])  # Координаты точки, в которой происходит отражение от стены

    reflected_vector = np.array([(rx_pos[0] - x_rfp), (rx_pos[1] - y_rfp), (rx_pos[2] - z_rfp)])
    reflected_vector_n = reflected_vector / la.norm(reflected_vector)

    # Azimuth angle computation for computation of attenuation
    # caused by deflection from polar direction
    tx_azimuth_0 = np.dot(d0_vector_tx_n, tx_dir_theta)
    rx_azimuth_0 = np.dot(d0_vector_rx_n, rx_dir_theta)
    tx_azimuth_1 = np.dot(d1_vector_tx_n, tx_dir_theta)
    rx_azimuth_1 = -1 * np.dot(d1_vector_rx_n, rx_dir_theta)  # Версия Андрея
    # rx_azimuth_1 = np.arccos(-1*np.dot(reflected_vector_n, rx_dir_theta))  # Моя версия

    # A grazing angle of NLoS ray for computation of reflection coefficient
    grazing_angle = -1 * np.dot(d1_vector_rx_n, ground_normal)  # Версия Андрея
    # grazing_angle = np.arccos(np.dot(reflected_vector_n, ground_normal)) #Моя версия

    relative_velocity = rx_velocity - tx_velocity
    velocity_pr_0 = np.dot(d0_vector_tx_n, relative_velocity)
    velocity_pr_1 = np.dot(d1_vector_tx_n, relative_velocity)

    # Attenuation caused by radiation pattern
    g0 = (tx_rp(azimuth=tx_azimuth_0, wavelen=wavelen, **kwargs) *
          rx_rp(azimuth=rx_azimuth_0, wavelen=wavelen, **kwargs))

    g1 = (tx_rp(azimuth=tx_azimuth_1, wavelen=wavelen, **kwargs) *
          rx_rp(azimuth=rx_azimuth_1, wavelen=wavelen, **kwargs))

    # Attenuation due to reflections (reflection coefficient) computation
    r1 = ground_reflection(cosine=grazing_angle, wavelen=wavelen, **kwargs)

    k = 2 * np.pi / wavelen

    pathloss = .5 / k * (g0 / d0 * np.exp(-1j * k * (d0 - time * velocity_pr_0)) +
                         r1 * g1 / d1 * np.exp(-1j * k * (d1 - time * velocity_pr_1)))
    # Короче, тут костыль, потому что я не помню, почему где-то ответ возводится в квадрат, а где-то нет,
    # поэтому я сделал два варианта return.
    if crutch:
        return (0.5 / k) ** 2 * np.absolute(g0 / d0 * np.exp(-1j * k * (d0 - time * velocity_pr_0)) +
                                            r1 * g1 / d1 * np.exp(-1j * k * (d1 - time * velocity_pr_1))) ** 2
    else:
        return to_power(pathloss) if log else pathloss


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
