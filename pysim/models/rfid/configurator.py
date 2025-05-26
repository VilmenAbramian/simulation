from tabulate import tabulate
import numpy as np

from pysim.models.rfid.handlers import start_simulation
from pysim.models.rfid.objects import Reader, Model, Antenna, Generator, Medium
from pysim.models.rfid.params import default_params, inner_params
import pysim.sim.simulator as sim


def create_model(
        print_params = False,
        **click_params
) -> Model:
    """
    Собирает и возвращает имитационную модель RFID на основе
    заданных параметров.

    Функция создает объект Model и инициализирует его компоненты:
    - считыватель (Reader),
    - антенну считывателя (Antenna),
    - среду распространения сигнала (Medium),
    - генератор меток (Generator).

    Приоритет параметров:
    1. Значения, переданные через `click_params` (например, из CLI).
    2. Значения по умолчанию из `RFIDDefaults` и `RFIDInternalParams`.

    Аргументы:
      print_params: Печатать или нет входные параметры модели
      **click_params: Переопределяемые параметры модели, такие как:
        - num_tags (int): число меток в симуляции;
        - tari (float): длительность импульса Tari;
        - encoding (str): тип кодирования ответа метки;
        - power (float): максимальная мощность передатчика, дБм;
        - tid_word_size (int): размер банка памяти для чтения;
        - useadjust (bool): включить или выключить QueryAdjust;
        - delta (float): шаг корректировки параметра Q;
        - speed (float): скорость считывателя, км/ч;
        - reader_offset, tag_offset, altitude: пространственные параметры
          (в метрах);
        - q (int): тестирование изменения Q

    Возвращает:
        Model: полностью настроенная модель RFID.
    """
    # 1) Создать объект модели
    model = Model()
    model.max_tags_num = click_params.get('num_tags', default_params.num_tags)
    model.update_interval = inner_params.geometry_params.update_interval
    model.statistics.use_power_statistics =(
        inner_params.energy_params.collect_power_statistics
    )

    # 2) Создать объект считывателя
    reader = Reader()
    model.reader = reader
    reader.tari = click_params.get('tari', default_params.tari)
    reader.tag_encoding = click_params.get('encoding', default_params.encoding)
    reader.rtcal = inner_params.reader_params.get_rtcal(reader.tari)
    reader.trcal = inner_params.reader_params.get_trcal(reader.rtcal)
    reader.delim = inner_params.reader_params.delim
    reader.temp = inner_params.reader_params.temp
    reader.session = inner_params.inventory_scenario_params.session
    reader.target = inner_params.inventory_scenario_params.target
    reader.sel = inner_params.inventory_scenario_params.sel
    reader.dr = inner_params.tag_params.dr
    reader.trext = inner_params.tag_params.trext
    reader.target_strategy = inner_params.inventory_scenario_params.target_strategy
    reader.rounds_per_target = inner_params.inventory_scenario_params.rounds_per_target
    reader.power_control_mode = inner_params.reader_power_params.get_power_control_mode()
    reader.max_power = click_params.get('power', default_params.power_dbm)
    reader.power_on_duration = inner_params.reader_power_params.reader_power_on_duration
    reader.power_off_duration = inner_params.reader_power_params.reader_power_off_duration
    reader.noise = inner_params.energy_params.reader_noise
    reader.read_tid_words_num = (
        click_params.get('tid_word_size', default_params.tid_word_size)
    )
    reader.read_tid_bank = (
        inner_params.inventory_scenario_params.read_tid_bank if reader.read_tid_words_num > 0 else False
    )
    reader.q = click_params.get('q', default_params.q)
    reader.use_query_adjust = click_params.get(
        'useadjust', default_params.useadjust
    )
    reader.adjust_delta = inner_params.reader_params.delta
    reader.q_fp = inner_params.reader_params.q_fp

    reader_antenna_x = click_params.get('reader_offset', default_params.reader_offset)
    reader_antenna_z = click_params.get('altitude', default_params.altitude)
    reader_antenna_y = 0
    tag_antenna_x = click_params.get('tag_offset', default_params.tag_offset)
    tag_antenna_z = inner_params.tag_params.tag_altitude

    # 3) Антенны для считывателя
    ant = Antenna()
    ant.pos = np.asarray([reader_antenna_x, reader_antenna_y, reader_antenna_z])
    ant.direction_theta = inner_params.geometry_params.reader_antenna_direction
    ant.gain = inner_params.energy_params.reader_antenna_gain
    ant.cable_loss = inner_params.energy_params.reader_cable_loss
    reader.attach_antenna(ant)

    # 4) Среда распространения сигнала
    medium = Medium()
    model.medium = medium
    medium.ber_distribution = inner_params.channel_params.ber_distribution
    medium.ground_reflection_type = inner_params.channel_params.ground_reflection_type
    medium.frequency = inner_params.channel_params.frequency_hz
    medium.permittivity = inner_params.channel_params.permittivity
    medium.conductivity = inner_params.channel_params.conductivity
    medium.polarization_loss = inner_params.energy_params.polarization_loss
    medium.use_doppler = inner_params.channel_params.use_doppler

    # 5) Генерация меток
    generator = Generator()
    model.generators.append(generator)
    generator.initial_position = np.asarray([
        tag_antenna_x,
        -inner_params.geometry_params.initial_distance_to_reader,
        tag_antenna_z
    ])
    generator.velocity = click_params.get('speed', default_params.speed)
    generator.direction = inner_params.geometry_params.movement_direction
    generator.tag_antenna_direction = inner_params.geometry_params.tag_antenna_direction
    generator.travel_distance = inner_params.geometry_params.travel_distance
    generator.epc_prefix = inner_params.tag_params.epc_prefix
    generator.tid_prefix = inner_params.tag_params.tid_prefix
    generator.epc_bitlen = inner_params.tag_params.epc_bitlen
    generator.tid_bitlen = inner_params.tag_params.get_tid_bitlen(reader.read_tid_words_num)
    generator.max_tags_generated = model.max_tags_num
    generator.antenna_gain = inner_params.energy_params.tag_antenna_gain
    generator.modulation_loss = inner_params.energy_params.tag_modulation_loss
    generator.sensitivity = inner_params.energy_params.tag_sensitivity
    generator.set_interval(
        inner_params.tag_params.generation_interval[0], # Функция
        *inner_params.tag_params.generation_interval[1:] # Её параметры
    )

    if print_params:
        print_model_settings()
    return model


def run_model(
    model: Model,
    logger_config: sim.ModelLoggerConfig,
    max_real_time: float | None = None,
    max_sim_time: float | None = None,
    max_num_events: int | None = None,
):
    """
    Запускает симуляцию модели RFID и возвращает результат моделирования.

    Аргументы:
        model: объект модели RFID, сконфигурированный для запуска;
        logger_config: настройки логирования для симуляции;
        max_real_time: максимальное время моделирования по реальному
          времени (в секундах);
        max_sim_time: максимальное симулируемое время (в секундах);
        max_num_events: максимальное количество событий, после которых
          симуляция будет завершена.

    Возвращает:
        result: объект с результатами моделирования.
    """
    sim_time, _, result = sim.run_simulation(
        sim.build_simulation(
            inner_params.model_name,
            init=start_simulation, # Первое запланированное событие
            context=model, # В качестве контекста используется объект модели
            max_real_time=max_real_time,
            max_sim_time=max_sim_time,
            max_num_events=max_num_events,
            logger_config=logger_config
        ))
    return result


def print_model_settings(model: Model) -> None:
    """
    Печатает таблицу всех параметров, используемых в текущей симуляции RFID.

    Отображаются параметры модели, считывателя, среды распространения (medium)
    и генератора меток.

    Аргументы:
        model: объект модели RFID, содержащий все компоненты и параметры.
    """
    reader = model.reader
    medium = model.medium
    generator = model.generators[0]

    def us(sec):
        return f'{sec * 1e6:.2f} us'

    rows = [
        # --- Model ----
        ('model', 'max_tags_num', model.max_tags_num),
        ('model', 'update_interval', model.update_interval),
        ('model', 'statistics.use_power_statistics',
         model.statistics.use_power_statistics),
        # --- Reader ---
        ('reader', 'tari', us(reader.tari)),
        ('reader', 'tag_encoding', reader.tag_encoding),
        ('reader', 'q', reader.q),
        ('reader', 'rtcal', us(reader.rtcal)),
        ('reader', 'trcal', us(reader.trcal)),
        ('reader', 'delim', us(reader.delim)),
        ('reader', 'temp', reader.temp),
        ('reader', 'session', reader.session),
        ('reader', 'target', reader.target),
        ('reader', 'sel', reader.sel),
        ('reader', 'dr', reader.dr),
        ('reader', 'trext', reader.trext),
        ('reader', 'target_strategy', reader.target_strategy),
        ('reader', 'rounds_per_target', reader.rounds_per_target),
        ('reader', 'power_control_mode', reader.power_control_mode),
        ('reader', 'max_power', reader.max_power),
        ('reader', 'power_on_duration', reader.power_on_duration),
        ('reader', 'power_off_duration', reader.power_off_duration),
        ('reader', 'noise', reader.noise),
        ('reader', 'read_tid_words_num', reader.read_tid_words_num),
        ('reader', 'read_tid_bank', reader.read_tid_bank),
        ('reader', 'always_start_with_first_antenna',
         reader.always_start_with_first_antenna),
        ('reader', 'antenna_switch_interval', reader.antenna_switch_interval),
        ('reader antenna', 'pos', reader.antenna.pos),
        ('reader antenna', 'direction_theta', reader.antenna.direction_theta),
        ('reader antenna', 'gain', reader.antenna.gain),
        ('reader antenna', 'cable_loss', reader.antenna.cable_loss),
        # --- Medium ---
        ('medium', 'ber_distribution', medium.ber_distribution),
        ('medium', 'ground_reflection_type', medium.ground_reflection_type),
        ('medium', 'frequency', medium.frequency),
        ('medium', 'permittivity', medium.permittivity),
        ('medium', 'conductivity', medium.conductivity),
        ('medium', 'polarization_loss', medium.polarization_loss),
        ('medium', 'use_doppler', medium.use_doppler),
        # --- Generator and tag ---
        ('tag', 'initial_position', generator.initial_position),
        ('tag', 'velocity', generator.velocity),
        ('tag', 'direction', generator.direction),
        ('tag', 'antenna_direction', generator.tag_antenna_direction),
        ('tag', 'travel_distance', generator.travel_distance),
        ('tag', 'epc_bitlen', generator.epc_bitlen),
        ('tag', 'tid_bitlen', generator.tid_bitlen),
        ('tag', 'antenna_gain', generator.antenna_gain),
        ('tag', 'modulation_loss', generator.modulation_loss),
        ('tag', 'sensitivity', generator.sensitivity),
        ('generator', 'num_tags', generator.max_tags_generated),
    ]
    print(tabulate(rows))
