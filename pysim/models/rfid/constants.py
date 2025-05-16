from pydantic import BaseModel, Field, confloat, conint
from typing import Literal


class RFIDDefaults(BaseModel):
    """
    Значения по умолчанию для параметров, которые могут
    быть изменены пользователем.
    """
    tari: Literal[6.25, 12.5, 18.75, 25.0] = Field(
        12.5, description="Длительность импульса data-0 (в микросекундах)."
                          "Выбирается из стандартных значений Gen2."
    )
    encoding: Literal['FM0', 'M2', 'M4', 'M8'] = Field(
        'M2', description="Тип модуляции, применяемый меткой для ответа."
                          "Выбор влияет на скорость передачи и устойчивость"
                          "к шуму."
    )
    tid_word_size: conint(ge=16, le=256, multiple_of=16) = Field(
        64, description="Размер TID/User банка в словах (16 бит на слово)."
                        "Определяет длину данных, которые читает считыватель."
    )
    power_dbm: confloat(ge=0, le=33) = Field(
        29.0, description="Мощность передатчика считывателя (в дБм)."
                          "Обычно 29 дБм = 800 мВт — максимум в Европе."
    )
    num_tags: conint(ge=10, le=10_000) = Field(
        50, description="Количество моделируемых меток в одной симуляции"
    )
    speed_kmph: confloat(ge=0, le=150) = Field(
        25.0, description="Скорость движения платформы"
                          "(например, БПЛА или автомобиля) в км/ч."
    )
    reader_offset: confloat(ge=0, le=10) = Field(
        3.0, description="Горизонтальное смещение считывателя от стены"
                         "(в метрах), от которой отражается сигнал."
    )
    tag_offset: confloat(ge=0, le=10) = Field(
        2.0, description="Горизонтальное смещение метки от стены (в метрах)."
    )
    altitude: confloat(ge=0, le=15) = Field(
        5.0, description="Высота полёта считывателя (в метрах)."
    )
    useadjust: bool = Field(
        False, description="Флаг, указывающий на использование QueryAdjust"
                           "команды (автоматическая корректировка Q)."
    )
    delta: confloat(gt=0.0) = Field(
        0.5, description=(
            "Коэффициент Δ для алгоритма QAdjust. Определяет чувствительность "
            "считывателя к коллизиям и пустым слотам при адаптации параметра Q."
            "Типичные значения: 0.1 < Δ < 0.5. Рекомендуется использовать"
            "меньшие значения Δ при больших Q и большие Δ при малых Q."
        )
    )


class RFIDInternalParams(BaseModel):
    """
    Внутренние параметры по умолчанию для модели RFID. Эти параметры задаются
    разработчиком модели и обычно не изменяются пользователем напрямую.
    """
    reader_noise: confloat(ge=-110, le=-60) = Field(
        -80.0, description="Шум в радиочастотной цепи считывателя, дБм."
    )
    reader_antenna_gain: confloat(ge=0, le=13) = Field(
        6.0, description="Усиление антенны считывателя, дБi."
    )
    reader_cable_loss: confloat(ge=-8, le=0) = Field(
        -2.0, description="Потери в кабеле считывателя, дБ."
    )
    tag_antenna_gain: confloat(ge=0, le=10) = Field(
        3.0, description="Усиление антенны метки, дБi."
    )
    tag_modulation_loss: confloat(ge=-20, le=0) = Field(
        -12.0, description="Потери мощности при модуляции ответного"
                           "сигнала метки, дБ."
    )
    tag_sensitivity: confloat(ge=-30, le=0) = Field(
        -18.0, description="Чувствительность метки, дБм."
    )
    frequency_hz: confloat(ge=820e6, le=950e6) = Field(
        860e6, description="Несущая частота считывателя, Гц."
    )
    permittivity: float = Field(
        15.0, description="Диэлектрическая проницаемость стены."
    )
    conductivity: float = Field(0.03, description="Проводимость стены.")
    polarization_loss: float = Field(
        -3.0, description="Потери, связанные с разными поляризациями"
                          "антенн считывателя и метки, дБ."
    )
    ber_distribution: Literal['rayleigh', 'awgn'] = Field(
        "rayleigh", description="Тип распределения помех при расчёте BER."
    )
    reader_power_on_duration: confloat(ge=1.0, le=60.0) = Field(
        2.0, description="Продолжительность активного периода"
                         "работы считывателя, сек."
    )
    reader_power_off_duration: confloat(ge=0.0, le=10.0) = Field(
        0.1, description="Пауза между включениями считывателя, сек."
    )
    # reader_antenna_switching_interval: float = Field(
    #     10.0, description="Интервал переключения антенн."
    # )
    # reader_always_start_with_first_antenna: bool = Field(False, description="Всегда ли начинать с антенны №1.")
    ground_reflection_type: Literal['reflection', 'const'] = Field(
        "reflection", description="Тип отражения от стены."
    ) # FIXME: переделать под переменную 'наличие стены, где const - отсутствие'
    use_doppler: bool = Field(True, description="Учитывать ли эффект Доплера.")
    epc_bitlen: conint(ge=8, le=256) = Field(
        96, description="Длина EPC-кода метки, бит."
    )
    rounds_per_target: conint(ge=1, le=1000) = Field(
        1, description="Число раундов перед сменой флага Target."
    )
    s1_persistence: float = Field(
        2.0, description="Как долго метка помнит своё состояние после"
                         "завершения сеанса считывания в сессии S1, сек."
    )
    s2_persistence: float = Field(
        2.0, description="Как долго метка помнит своё состояние после"
                         "завершения сеанса считывания в сессии S2, сек."
    )
    s3_persistence: float = Field(
        2.0, description="Как долго метка помнит своё состояние после"
                         "завершения сеанса считывания в сессии S3, сек."
    )
    update_interval: confloat(gt=0.05, le=0.05) = Field(
        0.01, description="Интервал обновления координат, сек."
    )
    travel_distance: confloat(ge=1.0, le=100.0) = Field(
        20.0, description="Путь метки от генерации до удаления, м."
    )
    initial_distance_to_reader: confloat(ge=0.1, le=20.0) = Field(
        10.0, description="Начальное расстояние до считывателя, м."
    )
    reader_antenna_direction: tuple[int, int, int] = Field(
        (0, 0, -1), description="Направление антенны считывателя"
                                "в 3D-пространстве."
    )
    tag_antenna_direction: tuple[int, int, int] = Field(
        (0, 0, 1), description="Направление антенны метки в 3D-пространстве."
    )
    rtcal_tari_mul: confloat(gt=2.5, le=3.0) = Field(
        3.0, description="Множитель RTcal (RTcal = rtcal_tari_mul * Tari).")
    trcal_rtcal_mul: confloat(gt=1.1, le=3) = Field(
        2.5, description="Множитель TRcal (TRcal = trcal_rtcal_mul * RTcal).")
    temp: Literal['NOMINAL', 'EXTENDED'] = Field(
        "NOMINAL", description="Температурный диапазон.")


default_params = RFIDDefaults()
inner_params = RFIDInternalParams()