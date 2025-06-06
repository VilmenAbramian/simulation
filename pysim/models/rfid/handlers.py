"""Обработчики событий для дискретно-событийной модели RFID."""

import numpy as np

from pysim.models.rfid.adjust_algs import *
from pysim.models.rfid.objects import Model, Reader, Tag, Transaction
import pysim.models.rfid.epcstd as std


def start_simulation(kernel):
    """
    Инициализация и запуск симуляции.

    При старте планирует 3 события (сортировка по времени):
      1) Запуск считывателя
      2) Генерация новой метки
      3) Обновить местоположения объектов

    Args:
        kernel: Ядро симуляции с контекстом модели.
    """
    assert isinstance(kernel.context, Model)
    context = kernel.context
    context.reader.kernel = kernel
    for generator in context.generators:
        kernel.schedule(
            generator.interval,
            generate_tag, (generator, ),
            msg="Генерация новой метки"
        )
    kernel.schedule(
        context.update_interval, update_positions, msg="Обновить расположение"
    )
    kernel.call(turn_reader_on, (context.reader,), msg="Запуск считывателя")


def _update_power(
        time: float, reader: Reader,
        tags, transaction,
        medium, statistics):
    """Обновляет мощность сигнала для меток и считывателя.

    В данном обработчике происходит запись информации об изменениях мощности
    в беспроводном канале связи между считывателем и меткой.

    Args:
        time: Текущее время симуляции;
        reader: Объект считывателя;
        tags: Список меток;
        transaction: Текущая транзакция (или None);
        medium: Среда передачи сигнала;
        statistics: Объект статистики;
    """
    for tag in tags:
        power = medium.estimate_tag_rx_power(reader, tag, time)
        tag.set_power(time, power)
        tag.pos += tag.velocity * tag.normalized_direction * (
            time - tag.last_pos_update
        )
        tag.last_pos_update = time

    if transaction is not None:
        for tag in transaction.tags:
            power = medium.estimate_reader_rx_power(reader, tag, time)
            transaction.reader_rx_power_map.update(tag, power)

    # Запись статистики (по умолчанию use_power_statistics=False)
    if statistics is not None and statistics.use_power_statistics:
        for tag in tags:
            tag_record = statistics.get_tag_record(tag)
            if tag_record:
                tag_record.write_power_record(time, reader, medium)
            else:
                raise ValueError(f"Попытка записи логов в"
                                 f"несуществующий журнал метки: {tag.tag_id}")


def _build_transaction(kernel, reader, reader_frame) -> Transaction:
    """
    Создаёт транзакцию на основе команды считывателя и ответов меток.

    В данном обработчике происходит запись информации об очередном
    раунде инвентаризации, в котором приняла участие метка

    Args:
        kernel: Ядро симуляции;
        reader: Объект считывателя;
        reader_frame: Команда считывателя.

    Returns:
        Transaction: Объект транзакции.
    """
    context = kernel.context
    all_responses = ((tag, tag.receive(reader_frame)) for tag in context.tags)
    tag_frames = [(tag, frame) for (tag, frame) in all_responses
                  if frame is not None]

    if context.tags and isinstance(reader_frame.command, std.Query):
        statistics = kernel.context.statistics
        participating_tags = [tag for tag in context.tags if tag.state in
                              {Tag.State.ARBITRATE, Tag.State.REPLY}]
        for tag in participating_tags:
            tag_record = statistics.get_tag_record(tag)
            if tag_record:
                tag_record.num_rounds_attained += 1
            else:
                raise ValueError(f"Попытка записи логов в"
                                 f"несуществующий журнал метки: {tag.tag_id}")

    now = kernel.time
    return Transaction(context.medium, reader, reader_frame, tag_frames, now)


def turn_reader_on(kernel, reader):
    ctx = kernel.context

    # Turning ON and getting the first command
    cmd_frame = reader.turn_on()

    # Managing antennas
    # В модели БПЛА у считывателя всегда одна антенна
    if reader.num_antennas > 1:
        reader.antenna_switch_event_id = kernel.schedule(
            reader.antenna_switch_interval, switch_reader_antenna, (reader, )
        )
        kernel.logger.debug(f'switched antenna #{reader.antenna_index}')

    # Updating tags and transaction power
    assert ctx.transaction is None
    _update_power(kernel.time, reader, ctx.tags, None, ctx.medium,
                  ctx.statistics)

    # Processing new command (reader frame)
    transaction = _build_transaction(kernel, reader, cmd_frame)
    ctx.transaction = transaction
    ctx.transaction.timeout_event_id = kernel.schedule(
        transaction.duration, finish_transaction, (transaction, ))
    if transaction.reply_start_time is not None:
        dt = transaction.reply_start_time - kernel.time
        kernel.schedule(dt, update_power_at_response_start, (transaction, ))

    # Scheduling turning off
    power_mode = reader.power_control_mode
    turned_on_duration = power_mode.min_powered_on_interval(reader)
    kernel.schedule(turned_on_duration, turn_reader_off, (reader, ))


def turn_reader_off(kernel, reader):
    ctx = kernel.context
    reader.turn_off()
    _update_power(kernel.time, reader, ctx.tags, None, ctx.medium,
                  ctx.statistics)

    # Clearing current transaction
    if ctx.transaction is not None:
        kernel.cancel(ctx.transaction.response_start_event_id)
        kernel.cancel(ctx.transaction.timeout_event_id)
        ctx.transaction = None

    # Clearing antenna switch event
    kernel.cancel(reader.antenna_switch_event_id)

    # Scheduling turning ON
    power_mode = reader.power_control_mode
    turned_off_duration = power_mode.powered_off_interval(reader)
    kernel.schedule(turned_off_duration, turn_reader_on, (reader, ))


def generate_tag(kernel, generator):
    assert isinstance(kernel.context, Model)

    if 0 <= generator.max_tags_generated <= generator.num_tags_generated:
        return

    # Creating a tag and adding it to the model
    ctx = kernel.context
    tag = generator.create_tag(kernel.context)
    tag.kernel = kernel
    tag.last_pos_update = kernel.time
    ctx.tags.append(tag)

    # Adding statistics record
    ctx.statistics.num_tags_created += 1
    generator.num_tags_generated += 1
    ctx.statistics.create_tag_record(tag)

    # Scheduling tag death (remove_tag) and next tag generation (this function)
    kernel.schedule(generator.lifetime, remove_tag, (tag, ))
    kernel.schedule(generator.interval, generate_tag, (generator, ))

    _update_power(kernel.time, ctx.reader, [tag], None, ctx.medium,
                  ctx.statistics)
    kernel.logger.info(
        f'(+) tag {tag.tag_id} created for {generator.lifetime}s: {str(tag)}'
    )


def remove_tag(kernel, tag):
    ctx = kernel.context
    ctx.tags.remove(tag)
    kernel.logger.info(f'(x) tag {tag.tag_id} died')
    ctx.num_tags_simulated += 1
    if (ctx.max_tags_num is not None and
            ctx.num_tags_simulated >= ctx.max_tags_num):
        kernel.stop()
    # Closing statistics record
    ctx.statistics.close_tag_record(tag)


def update_positions(kernel):
    ctx = kernel.context

    kernel.schedule(kernel.context.update_interval, update_positions)
    _update_power(kernel.time, ctx.reader, ctx.tags, ctx.transaction,
                  ctx.medium, ctx.statistics)


def _no_tag_response(kernel, ctx, reader):
    """
    Обработка отсутствия ответа метки после завершения транзакции считывателя
    """
    cmd_frame = apply_query_adjust(kernel, reader, direction=-1)
    if cmd_frame is None:
        cmd_frame = ctx.reader.timeout()
    return cmd_frame


def _one_tag_response(kernel, transaction, ctx, reader, tag, frame, snr, ber):
    '''
    Обработка единственного ответа от метки после
    завершения транзакции считывателя
    '''
    if isinstance(frame.reply, std.AckReply):
        tag_read_record = (
            ctx.statistics.get_tag_record(tag)
            .new_tag_read_record(reader, reader.inventory_round.index))
        tag_read_record.tag_pos = np.array(tag.pos, copy=True)
        tag_read_record.reader_antenna_pos = np.array(
            reader.antenna.pos, copy=True)
        tag_read_record.ber = ber
        tag_read_record.snr = snr

        # noinspection PyShadowingNames
        def on_slot_end(round_index, slot_index, reader, tag, statistics):
            statistics.get_tag_record(tag).close_tag_read_record()
            reader.slot_finish_listeners.remove(
                statistics.slot_end_listener_id)

        ctx.statistics.slot_end_listener_id = \
            ctx.reader.slot_finish_listeners.add(
                on_slot_end, reader=reader, tag=tag,
                statistics=ctx.statistics)

        kernel.logger.info(
            '---> Received tag data: EPC={}, received power={} from tag {}'
            ''.format(
                ''.join('{:02X}'.format(b) for b in frame.reply.epc),
                transaction.reader_rx_power_map.get(tag),
                tag.tag_id
            )
        )

    if isinstance(frame.reply, std.ReadReply):
        tag_read_record = ctx.statistics.get_tag_record(tag).tag_read_record
        tag_read_record.read_tid = True

        kernel.logger.info(
            '---> Received TID: memory={}, received power={} from tag {}'
            ''.format(
                ''.join('{:02X}'.format(b) for b in frame.reply.memory),
                transaction.reader_rx_power_map.get(tag), tag.tag_id))

    return ctx.reader.receive(frame)


def _multiple_tag_response(kernel, ctx, reader, transaction):
    """Обработка коллизии"""
    for tag in transaction.tags:
        tag_record = ctx.statistics.get_tag_record(tag)
        if tag_record:
            tag_record.collision_count += 1

    cmd_frame = apply_query_adjust(kernel, reader, direction=1)
    return cmd_frame if cmd_frame is not None else ctx.reader.timeout()


def apply_query_adjust(kernel, reader, direction: int):
    """
    Применение алгоритма QueryAdjust.

    direction = +1 для увеличения Q (коллизия);
    direction = -1 для уменьшения Q (пустой слот).
    """
    if (
        reader.use_query_adjust and
        reader.state in (Reader.State.QUERY, Reader.State.QREP) and
        0 <= reader.q <= 15
    ):

        strategy =  QueryAdjustStrategy.STATIC
        adjust_fn = QUERY_ADJUST_FUNCTIONS.get(strategy, static_query_adjust)
        reader.q_fp = adjust_fn(reader.q_fp, direction, reader.q)
        kernel.logger.error(f"Q с плавающей точкой: {reader.q_fp}")
        new_q = round(reader.q_fp)

        if abs(reader.q - new_q) == 1:
            direction_str = "увеличил" if direction > 0 else "уменьшил"
            kernel.logger.error(f'Считыватель {direction_str} Q с {reader.q} до {new_q}')
            reader.q = new_q
            reader.updn = direction
            cmd_frame = reader.set_state(Reader.State.QAdjust)
            reader.updn = 0
            return cmd_frame
    return None


def finish_transaction(kernel, transaction):
    kernel.logger.debug(f'finished transaction: {str(transaction)}')
    ctx = kernel.context
    reader = ctx.reader
    assert transaction is ctx.transaction
    cmd_frame = None

    if len(transaction.replies) > 1:
        # Коллизия
        # kernel.logger.error('Коллизия!')
        cmd_frame = _multiple_tag_response(kernel, ctx, reader, transaction)

    tag, frame, snr, ber = transaction.received_tag_frame(
        ctx.medium, kernel.time)

    if frame is not None:
        # Если есть один ответ от метки
        cmd_frame = _one_tag_response(
            kernel, transaction, ctx, reader, tag, frame, snr, ber
        )
    elif frame is None and cmd_frame is None:
        # Если нет ответа от метки
        cmd_frame = _no_tag_response(kernel, ctx, reader)

    # Processing new command (reader frame)
    ctx.transaction = _build_transaction(kernel, ctx.reader, cmd_frame)
    ctx.transaction.timeout_event_id = kernel.schedule(
        transaction.duration, finish_transaction, (ctx.transaction, )
    )
    if transaction.reply_start_time is not None:
        dt = transaction.reply_start_time - kernel.time
        kernel.schedule(dt, update_power_at_response_start, (transaction, ))


def switch_reader_antenna(kernel, reader):
    antenna = reader.select_next_antenna()
    kernel.logger.debug(f'switched antenna #{antenna.index}')
    reader.antenna_switch_event_id = kernel.schedule(
        reader.antenna_switch_interval, switch_reader_antenna, (reader, )
    )


def update_power_at_response_start(kernel, transaction):
    ctx = kernel.context
    _update_power(kernel.time, ctx.reader, ctx.tags, transaction, ctx.medium,
                  ctx.statistics)
    transaction.response_start_event_id = None
