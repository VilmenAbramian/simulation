from dataclasses import dataclass
import random
from typing import Any, Optional

from .objects import Config
from pysim.sim import Simulator
from pysim.sim.logger import ModelLogger


STATE_CODES = {
    'Arbitrate': 0,
    'Reply': 1,
    'Acknowledged': 2,
    'Secured': 3,
    'Final': 4
}

STATE_CODES_REVERSE = { # Нужен для читаемости логов
    0: 'Arbitrate',
    1: 'Reply',
    2: 'Acknowledged',
    3: 'Secured',
    4: 'Final'
}


class Model:
    '''
    Объект модели содержит все 4 состояния метки +
    1 состояние, когда чтение полностью завершилось
    и мы попали в так называемое "состояние поглощения"
    '''
    def __init__(self, config: Config, logger: ModelLogger):
        self.config = config
        self.arbitrate = State(
            name = STATE_CODES['Arbitrate'],
            next_state_probability = config.probability[0],
            processing_time = config.processing_time[0],
            max_transmisions = config.max_transmisions
        )
        self.reply = State(
            name = STATE_CODES['Reply'],
            next_state_probability = config.probability[1],
            processing_time = config.processing_time[1],
            max_transmisions = config.max_transmisions
        )
        self.acknowledged = State(
            name = STATE_CODES['Acknowledged'],
            next_state_probability = config.probability[2],
            processing_time = config.processing_time[2],
            max_transmisions = config.max_transmisions
        )
        self.secured = State(
            name = STATE_CODES['Secured'],
            next_state_probability = config.probability[3],
            processing_time = config.processing_time[3],
            max_transmisions = config.max_transmisions
        )
        self.final = State(
            name = STATE_CODES['Final'],
            next_state_probability = 0,
            processing_time = 0,
            max_transmisions = None
        )

        # Делаем запись в журнал
        logger.debug('Модель успешно сконфигурирована')
    
    def choose_state(self, state_number):
        '''
        Метод для вызова объекта нужного состояния.
        Нужен для того, чтобы из одного состояния 
        вызвать другое.
        '''
        if state_number == STATE_CODES['Arbitrate']:
            return self.arbitrate
        elif state_number == STATE_CODES['Reply']:
            return self.reply
        elif state_number == STATE_CODES['Acknowledged']:
            return self.acknowledged
        elif state_number == STATE_CODES['Secured']:
            return self.secured
        elif state_number == STATE_CODES['Final']:
            return self.final


@dataclass
class Packet:
    present_state: Any
    number: int


class State():
    '''
    Одно из 4х состояний метки + 1 дополнительное 
    состояние, когда метка передала всю информацию
    и работа с ней завершена
    '''
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
        
        if self.name == 0:
            self.number: int = random.randint(a=0, b=1_000_000)
        self.packet: Packet = None

        # Statistics:
        self.num_pakage_sent = 0
        self.num_resent = 0
        self.total_time_in_state = 0

    def handle_timeout(self, sim: Simulator, packet: Packet = None) -> None:
        """
        При достижении таймаута метка рассчитывает, успешно ли она изменила своё состояние,
        увеличивает счетчик пакетов и начинает передачу.

        Args:
            sim (Simulator): экземпляр симулятора
        """

        if self.name == 0:
            packet = Packet(
                present_state = self.name,
                number = self.number
            )
            sim.logger.debug(f'Создан пакет с номером: {self.number}')
            self.number += 1

        if self.max_transmisions is None or self.num_pakage_sent < self.max_transmisions:
            sim.logger.debug(f'Время обработки вышло, отправка пакета № {packet.number}')
            if random.random() > self.probability:
                # Метка осталась в текущем состоянии
                sim.logger.debug(f'Неудачная передача пакета № {packet.number}')
                sim.logger.info(f'Метка осталась в состоянии {STATE_CODES_REVERSE[self.name]}')
                sim.schedule(self.interval, self.handle_timeout, (packet,))
                # sim.schedule(self.interval, self.handle_timeout)
            else:
                # Метка изменила состояние
                sim.logger.info(f'Изменение состояния метки с {STATE_CODES_REVERSE[self.name]}')
                next_state = self.calculate_next_state(self.name)
                sim.call(sim.context.choose_state(next_state).handle_receive, (packet,))
        else:
            # Если достигли максимального числа пакетов, останавливаемся.
            sim.logger.info("reached max pings (%d), stopping", self.max_transmisions)
            sim.stop()

    def handle_receive(self, sim: Simulator, packet: Packet):
        sim.logger.debug(f'Принят пакет № {packet.number} от состояния {STATE_CODES_REVERSE[packet.present_state]}')
        sim.logger.info(f'Состояние изменено на {STATE_CODES_REVERSE[self.name]}')
        packet.present_state = self.name
        self.num_pakage_sent += 1
        if self.name == 4:
            sim.call(sim.context.arbitrate.handle_timeout)
            sim.logger.warning(f'Отправлено заявок: {self.num_pakage_sent}')
        else:
            sim.schedule(self.interval, self.handle_timeout, (packet,))
        # self.intervals_list.append(self.interval)

    def calculate_next_state(self, name):
        if name >= 4:
            raise 'Такого состояния не существует!'
        return name + 1

    def __str__(self):
        return f'Состояние метки: {self.name}'
