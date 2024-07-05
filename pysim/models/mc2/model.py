from dataclasses import dataclass
import random
from typing import Any, Optional

from pysim.sim.logger import ModelLogger
from .objects import Config
from pysim.sim import Simulator


state_codes = {
    0: 'Arbitrate',
    1: 'Reply',
    2: 'Acknowledged',
    3: 'Secured',
    4: 'Final'

}

class Model:
    def __init__(self, config: Config, logger: ModelLogger):
        self.config = config
        self.arbitrate = State(
            name = state_codes[0],
            next_state_probability = config.probability[0],
            processing_time = config.processing_time[0],
            max_transmisions = config.max_transmisions
        )
        self.reply = State(
            name = state_codes[1],
            next_state_probability = config.probability[1],
            processing_time = config.processing_time[1],
            max_transmisions = config.max_transmisions
        )
        self.acknowledged = State(
            name = state_codes[2],
            next_state_probability = config.probability[2],
            processing_time = config.processing_time[2],
            max_transmisions = config.max_transmisions
        )
        self.secured = State(
            name = state_codes[3],
            next_state_probability = config.probability[3],
            processing_time = config.processing_time[3],
            max_transmisions = config.max_transmisions
        )
        self.final = State(
            name = state_codes[4],
            next_state_probability = 0,
            processing_time = 0,
            max_transmisions = None
        )

        # self.client.set_server(self.server)
        # self.client.set_channel(self.channel)
        # self.server.set_channel(self.channel)

        # Делаем запись в журнал
        logger.debug('Модель успешно сконфигурирована')


class Test:
    ...


@dataclass
class Packet:
    present_state: Any
    number: int


class State():
    """
    Arbitrate состояние метки
    """
    def __init__(
        self,
        name: str,
        next_state_probability: float,
        processing_time: float,
        max_transmisions: int | None
    ):
        self.name = name
        self.code: int = None # Номер состояния метки
        self.probability = next_state_probability
        self.interval = processing_time
        self.max_transmisions = max_transmisions

        self.number: int = random.randint(a=0, b=1_000_000)
        self.packet: Packet = None

        # Statistics:
        self.num_pakage_sent = 0
        self.num_resent = 0
        self.total_time_in_state = 0

    def handle_timeout(self, sim: Simulator) -> None:
        """
        При достижении таймаута отправитель рассчитывает, получил ли он
        пакет, увеличивает счетчик пакетов и начинает передачу.

        Args:
            sim (Simulator): экземпляр симулятора
        """

        if self.name == 'Arbitrate':
            packet = Packet(
                present_state = self.name,
                number = self.number
            )
            self.number += 1

        if self.max_transmisions is None or self.max_transmisions < self.max_transmisions:
            sim.logger.debug('state timeout, sending packet #%d', self.number)
            if random.random() > self.next_state_probability:
                # Метка осталась в текущем состоянии
                sim.logger.info('sending fail #%d', self.number)
            else:
                # Метка изменила состояние
                sim.logger.info('change state #%d', self.number)
        #     sim.call(self.channel.send, (packet,))

        #         sim.schedule(
        #         self.interval,
        #         sim.context.,
        #         (packet,),
        #         msg=f"{packet.sender} --({packet.number})--> {packet.receiver}"
        # )
        #     self.num_pings_sent += 1
        else:
            # Если достигли максимального числа пакетов, останавливаемся.
            sim.logger.info("reached max pings (%d), stopping", self.max_transmisions)
            sim.stop()

    def handle_receive(self, sim: Simulator, packet: Packet):
        """
        Обработка события получения Pong-а. Проверяем, совпадает ли
        полученный номер. Если совпадает, считаем ответ полученным. Иначе,
        игнорируем (запоминаем в num_bad_pongs).

        Args:
            sim (Simulator): экземпляр симулятора
            packet (Packet): число из Pong-а
        """
        if packet.number == self.number:
            sim.logger.debug("client received pong (good)")
            self.was_acknowledged = True
            self.num_acknowledged += 1
        else:
            sim.logger.debug("client received wrong pong")
            self.num_bad_pongs += 1
        sim.schedule(self.interval, self.handle_timeout, )
        self.intervals_list.append(self.interval)

    def calculate_next_state():
        ...

    def __str__(self):
        return "client"
