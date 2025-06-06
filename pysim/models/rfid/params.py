from enum import Enum
from pydantic import BaseModel, Field, confloat, conint
from typing import Any, Callable, Literal

import pysim.models.rfid.epcstd as std
from pysim.models.rfid.objects import Reader

KMPH_TO_MPS_MUL = 1.0 / 3.6


class Polarization(float, Enum):
    VERTICAL = 0.0
    HORIZONTAL = 1.0
    CIRCULAR = 0.5


class RFIDDefaults(BaseModel):
    """
    Значения по умолчанию для параметров, которые могут
    быть изменены пользователем через консольный click-интерфейс.

    Для моделирования графиков в дипломе использовалось num_tags = 6000
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
    speed: confloat(ge=0, le=150) = Field(
        25.0, description="Скорость движения платформы"
                          "(например, БПЛА или автомобиля) в км/ч."
    )
    reader_offset: confloat(ge=0, le=10) = Field(
        2.0, description="Горизонтальное смещение считывателя от стены"
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
    q: conint(ge=0, le=15) = Field(
        5, description='Значение параметра Q в начале моделирования'
    )


    @staticmethod
    def parse_tag_encoding(s: str) -> std.TagEncoding:
        """
        Преобразует строковое представление модуляции метки в
        соответствующее TagEncoding.

        Поддерживаются как числовые значения ('1', '2', '4', '8'),
        так и строковые ('FM0', 'M2', 'M4', 'M8').

        Args:
            s: Строка, обозначающая тип модуляции.

        Returns:
            std.TagEncoding: Перечисление, соответствующее типу модуляции.

        Raises:
            ValueError: Если переданное значение не распознано.
        """
        s = s.upper()
        if s in {'1', "FM0"}:
            return std.TagEncoding.FM0
        elif s in {'2', 'M2'}:
            return std.TagEncoding.M2
        elif s in {'4', 'M4'}:
            return std.TagEncoding.M4
        elif s in {'8', 'M8'}:
            return std.TagEncoding.M8
        else:
            raise ValueError('illegal encoding = {}'.format(s))


class ReaderParams(BaseModel):
    """Настройки параметров RFID считывателя."""
    delim: float = Field(
        12.5e-6, description="Длительность символа-разделителя (Delim), сек."
    )
    temp: Literal['NOMINAL', 'EXTENDED'] = Field(
        "NOMINAL", description="Температурный диапазон.")
    # --- Настройки для симуляции с коллизиями ---
    delta: confloat(gt=0.0) = Field(
        0.5, description=(
            "Коэффициент Δ для алгоритма QAdjust. Определяет чувствительность "
            "считывателя к коллизиям и пустым слотам при адаптации параметра Q."
            "Типичные значения: 0.1 < Δ < 0.5. Рекомендуется использовать"
            "меньшие значения Δ при больших Q и большие Δ при малых Q."
        )
    )
    q_fp: confloat(ge=0.0, le=15.0) = Field(
        RFIDDefaults().q, description='Дробное значение Q для алгоритма'
                       'коррекции Q в QueryAdjust'
    )
    # -----------------------------------------------
    rtcal_tari_mul: confloat(gt=2.5, le=3.0) = Field(
        3.0, description="Множитель RTcal (RTcal = rtcal_tari_mul * Tari).")
    trcal_rtcal_mul: confloat(gt=1.1, le=3) = Field(
        2.5, description="Множитель TRcal (TRcal = trcal_rtcal_mul * RTcal).")

    @property
    def rtcal(self) -> float:
        """
        RTcal (Interrogator-to-Tag calibration symbol).
        RTcal = 0_length + 1_length.
        """
        return self.get_rtcal(self.tari)

    def get_rtcal(self, tari: float) -> float:
        return tari * self.rtcal_tari_mul

    @property
    def trcal(self) -> float:
        """
        Определён в стандарте RFID для вычисления частоты сигнала меток
        BLF Backscatter-link frequency (BLF = DR/TRcal)
        """
        return self.get_trcal(self.rtcal)

    def get_trcal(self, rtcal: float) -> float:
        return rtcal * self.trcal_rtcal_mul


class GeometryParams(BaseModel):
    """Геометрические параметры RFID системы в 3-х мерном пространстве."""
    dimension_of_space: int = Field(
        3, description="Размерность пространства моделирования."
    )
    grid_step: conint(ge=50, le=1000) = Field(
        200, description="Разрешение сетки для расчёта зоны активности метки."
                         "Также используется для других графиков оценки канала"
    )
    initial_distance_to_reader: confloat(ge=0.1, le=20.0) = Field(
        5.0, description="Начальное расстояние метки до считывателя, м."
    )
    movement_direction: tuple[float, float, float] = Field(
        (0, 1, 0), description='Единичный вектор направления движения.'
    )
    travel_distance: confloat(ge=1.0, le=100.0) = Field(
        20.0, description="Путь метки от генерации до удаления, м."
    )
    reader_antenna_direction: tuple[int, int, int] = Field(
        (0, 0, -1), description="Направление антенны считывателя"
                                "в 3D-пространстве."
    )
    tag_antenna_direction: tuple[int, int, int] = Field(
        (0, 0, 1), description="Направление антенны метки в 3D-пространстве."
    )
    speed_of_light: int = Field(
        299_792_458, description="Скорость света, м/с"
    )
    update_interval: confloat(gt=0.05, le=0.05) = Field(
        0.01, description="Интервал обновления времени в симуляции"
                          "(квант времени модели), сек."
    )


class EnergyParams(BaseModel):
    """Энергетические параметры моделируемой системы."""
    reader_antenna_gain: confloat(ge=0, le=13) = Field(
        6.0, description="Усиление антенны считывателя, дБi."
    )
    reader_cable_loss: confloat(ge=-8, le=0) = Field(
        -2.0, description="Потери в кабеле считывателя, дБ."
    )
    reader_noise: confloat(ge=-110, le=-60) = Field(
        -80.0, description="Шум в радиочастотной цепи считывателя, дБм."
    )
    reader_sensitivity: confloat(ge=-95, le=-75) = Field(
        -80.0, description="Чувствительность радиоприёмника считывателя, дБм."
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
    polarization_loss: float = Field(
        -3.0, description="Потери, связанные с разными поляризациями"
                          "антенн считывателя и метки, дБ."
    )
    thermal_noise: confloat(ge=-125, le=-105) = Field(
        -114, description="Мощность теплового шума в полосе 1МГц для"
                          "температуры около 17C, дБм."
    )
    collect_power_statistics: bool = Field(
        False, description="Вести ли журнал _TagPowerRecord для отслеживания"
                           "параметров канала в течении симуляции."
    )


class ChannelParams(BaseModel):
    """Параметры RFID канала."""
    frequency_hz: confloat(ge=820e6, le=950e6) = Field(
        860e6, description="Несущая частота считывателя, Гц."
    )
    permittivity: float = Field(
        15.0, description="Диэлектрическая проницаемость стены."
    )
    conductivity: float = Field(0.03, description="Проводимость стены.")
    ber_distribution: Literal['rayleigh', 'awgn'] = Field(
        "rayleigh", description="Тип распределения помех при расчёте BER."
    )
    # FIXME: переделать под переменную 'наличие стены, где const - отсутствие'
    ground_reflection_type: Literal['reflection', 'const'] = Field(
        "reflection", description="Тип отражения от стены."
    )
    use_doppler: bool = Field(True, description="Учитывать ли эффект Доплера.")
    vertical_polarization: float = Field(
        Polarization.VERTICAL.value, description="Вертикальная поляризация антенны."
    )
    horizontal_polarization: float = Field(
        Polarization.HORIZONTAL.value, description="Горизонтальная поляризация антенны."
    )
    circular_polarization: float = Field(
        Polarization.CIRCULAR.value, description="Круговая поляризация антенны"
    )
    reader_default_polarization: float = Field(
        Polarization.CIRCULAR.value, description="Поляризация антенны считывателя по умолчанию"
    )
    tag_default_polarization: float = Field(
        Polarization.HORIZONTAL.value, description="Поляризация антенны метки по умолчанию"
    )

class ReaderPowerParams(BaseModel):
    """
    Параметры периодической работы считывателя.
    """
    reader_switch_power: bool = True
    reader_power_on_duration: confloat(ge=1.0, le=60.0) = Field(
        2.0, description="Продолжительность активного периода"
                         "работы считывателя, сек."
    )
    reader_power_off_duration: confloat(ge=0.0, le=10.0) = Field(
        0.1, description="Пауза между включениями считывателя, сек."
    )

    def get_power_control_mode(
        self, reader_switch_power: bool | None = None
    ) -> Reader.PowerControlMode:
        """
        Возвращает режим управления питанием считывателя.

        Если флаг reader_switch_power равен True, считыватель работает
        в периодическом режиме (включается и выключается с заданным
        интервалом). Если False — работает непрерывно. Значение по умолчанию
        берётся из параметра self.reader_switch_power.
        """
        x = (reader_switch_power if reader_switch_power is not None
             else self.reader_switch_power)
        return (Reader.PowerControlMode.PERIODIC if x
                else Reader.PowerControlMode.ALWAYS_ON)


class InventoryScenarioParams(BaseModel):
    """Настройки сценария (алгоритма) опроса меток считывателем."""
    read_tid_bank: bool = Field(
        True, description='Нужно ли дополнительно читать банк данных TID после'
                          'идентификации метки (чтения EPCID метки)'
    )
    sel: std.SelFlag = std.SelFlag.ALL  # флаг Sel (не используется в модели)
    session: std.Session = Field(
        std.Session.S0, description="Номер сессии, в которой идет опрос"
    )
    target: std.InventoryFlag = Field(
        std.InventoryFlag.A,
        description=(
            "Флаг сессии (поле Target команды Query), по которому идет опрос"
            "меток. Ответ передают только метки с совпадающим флагом."
            "После каждого ответа на ACK метка инвертирует свой флаг сессии"
            "(A → B или B → A). Если в следующем раунде считыватель"
            "запрашивает тот же Target, метка не участвует в опросе."
        )
    )
    target_strategy: Literal["const", "switch"] = Field(
        "switch",
        description="Стратегия выбора флага сессии. 'const' — фиксированный"
                    "Target, 'switch' — чередование каждые"
                    "rounds_per_target раундов значения поля Target."
    )
    rounds_per_target: conint(ge=1, le=1000) = Field(
        1, description="Число раундов перед сменой флага Target."
    )


class TagParams(BaseModel):
    """
    Настройки параметров RFID метки.

    Параметры s<n>_persistence определяют, через сколько времени без питания
    метка сбросит в A хранящийся флаг сессии. Для сессии S0 такого параметра
    нет, так как по стандарту EPC Class 1 Gen.2 метка должна сбросить в A
    флаг сессии S0 сразу после потери питания.
    """
    dr: std.DivideRatio = Field(
        std.DivideRatio.DR_8, description="Коэффициент DR (8 или 64/3)"
    )
    epc_prefix: str = Field("AAAA", description="Префикс EPC-кода метки.")
    tid_prefix: str = Field("AAAA", description="Префикс TID-кода метки.")
    trext: bool = Field(
        True, description="Использовать ли в ответах расширенную преамбулу"
    )
    epc_bitlen: conint(ge=8, le=256) = Field(
        96, description="Длина EPC-кода метки, бит."
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
    tag_altitude: float = Field(
        0.0, description="В модели БПЛА метка всегда лежит на земле"
    )
    generation_interval: tuple[Callable[..., float], Any] = Field(
        default=(lambda: 1.0,),
        description=(
            "Функция и её параметры, определяющие интервал появления новой"
            "метки. Если функция не требует аргументов, используется кортеж"
            "с одним элементом: (функция,). Если функция принимает аргументы,"
            "они перечисляются следом: (функция, arg1, arg2, ...)."
            "Например: (numpy.random.exponential, 42.0) — интервал"
            "с экспоненциальным распределением со средним 42."
        )
    )

    @property
    def tid_bitlen(self) -> int:
        """Количество бит, считываемых с метки, при чтении банка памяти."""
        return self.get_tid_bitlen(self.tid_word_size)

    def get_tid_bitlen(self, tid_word_size: int) -> int:
        return tid_word_size * 16


class RFIDInternalParams(BaseModel):
    """
    Внутренние параметры по умолчанию для модели RFID.

    Эти параметры задаются разработчиком модели и обычно
    не изменяются пользователем напрямую.
    """
    model_name: str = 'RFID'
    reader_params: ReaderParams = Field(default_factory=ReaderParams)
    geometry_params: GeometryParams = Field(default_factory=GeometryParams)
    energy_params: EnergyParams = Field(default_factory=EnergyParams)
    channel_params: ChannelParams = Field(default_factory=ChannelParams)
    reader_power_params: ReaderPowerParams = Field(
        default_factory=ReaderPowerParams
    )
    inventory_scenario_params: InventoryScenarioParams = Field(
        default_factory=InventoryScenarioParams
    )
    tag_params: TagParams = Field(default_factory=TagParams)


default_params = RFIDDefaults()
inner_params = RFIDInternalParams()