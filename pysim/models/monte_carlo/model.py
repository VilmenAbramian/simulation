from dataclasses import dataclass
import random
from typing import Any

from .objects import Config
from pysim.sim import Simulator
from pysim.sim.logger import ModelLogger


STATE_CODES = {
    'Arbitrate': 0,
    'Reply': 1,
    'Acknowledged': 2,
    'Secured': 3,
    'Final': 4,
}

STATE_CODES_REVERSE = {  # Нужен для читаемости логов
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
        self.scenario = config.scenario
        self.arbitrate = State(
            code=STATE_CODES['Arbitrate'],
            next_state_probability=config.probability[0],
            processing_time=config.processing_time[0],
            max_transmisions=config.max_transmisions,
            scenario=config.scenario
        )
        self.reply = State(
            code=STATE_CODES['Reply'],
            next_state_probability=config.probability[1],
            processing_time=config.processing_time[1],
            max_transmisions=config.max_transmisions,
            scenario=config.scenario
        )
        self.acknowledged = State(
            code=STATE_CODES['Acknowledged'],
            next_state_probability=config.probability[2],
            processing_time=config.processing_time[2],
            max_transmisions=config.max_transmisions,
            scenario=config.scenario
        )
        if self.scenario == 3:
            self.chunks_number = config.chunks_number
            self.secured = []
            for i in range(self.chunks_number):
                secured_state = State(
                    code=STATE_CODES['Secured'],
                    next_state_probability=config.probability[3],
                    processing_time=config.processing_time[3],
                    max_transmisions=config.max_transmisions,
                    scenario=config.scenario,
                    secured_number=i
                )
                self.secured.append(secured_state)
            self.chunks_passed = 0
        else:
            self.secured = State(
                code=STATE_CODES['Secured'],
                next_state_probability=config.probability[3],
                processing_time=config.processing_time[3],
                max_transmisions=config.max_transmisions,
                scenario=config.scenario
            )
        self.final = State(
            code=STATE_CODES['Final'],
            next_state_probability=0,
            processing_time=0,
            max_transmisions=None,
            scenario=config.scenario
        )
        self.num_transmissions = 0

        # Делаем запись в журнал
        logger.debug(
            f'Модель в режиме №{self.scenario} успешно сконфигурирована'
        )

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
    '''
    Гипотетический пакет, который "передаётся" из
    состояния в состояние метки, как если бы они были
    различными устройствами, передающими информацию друг
    другу посредством таких пакетов.

    На самом деле метка переходит из одного состояния в
    другое в процессе общения со считывателем.
    '''
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
        code: int,
        next_state_probability: float,
        processing_time: float,
        max_transmisions: int | None,
        scenario: int,
        secured_number=None  # Для 3го сценария
    ):
        self.code = code  # Номер состояния метки
        self.probability = next_state_probability
        self.interval = processing_time
        self.max_transmisions = max_transmisions
        self.scenario = scenario
        self.secured_number = secured_number

        if self.code == 0:
            self.number: int = random.randint(a=0, b=1_000_000)
        self.packet: Packet = None

        # Statistics:
        self.num_pakage_sent = 0

    def success_state_change(self, sim, packet):
        '''
        Изменение состояния метки прошло успешно
        '''
        sim.logger.info(
            'Изменение состояния метки с '
            f'{STATE_CODES_REVERSE[self.code]}'
        )
        if (self.scenario == 3 and self.code in (2, 3) and
                sim.context.chunks_passed < sim.context.chunks_number):
            # В случае 3го сценария переключаемся между "чанками"
            sim.logger.info(
                f'Метка успешно передала "чанк" номер {self.secured_number}'
            )
            sim.schedule(
                self.interval,
                sim.context.secured[sim.context.chunks_passed].handle_receive,
                (packet,)
            )
        else:
            next_state = self.calculate_next_state(self.code)
            sim.schedule(
                self.interval,
                sim.context.choose_state(
                    next_state
                ).handle_receive, (packet,)
            )

    def faild_state_change(self, sim, packet):
        '''
        Метка не смогла изменить состояние прямым путём
        в результате чего она в зависимости от выбранного
        сценария моделирования она либо возвращается в
        исходное состояние, либо остаётся в текущем
        '''
        sim.logger.debug(
            f'Неудачная передача пакета № {packet.number}'
        )
        if self.scenario == 1:
            # По первому сценарию метка возвращается в исходное состояние
            sim.logger.info(
                    'Метка возвращается в исходное состояние!'
                )
            next_state = 0
            sim.schedule(
                sim.context.arbitrate.interval,
                sim.context.choose_state(
                    next_state
                ).handle_receive, (packet,)
            )
        elif self.scenario in (2, 3):
            # По второму сценарию метка остаётся в текущем состоянии
            sim.logger.info(
                'Метка осталась в состоянии '
                f'{STATE_CODES_REVERSE[self.code]}'
            )
            sim.schedule(self.interval, self.handle_timeout, (packet,))

    def handle_timeout(self, sim: Simulator, packet: Packet = None) -> None:
        '''
        При достижении таймаута метка рассчитывает,
        успешно ли она изменила своё состояние, если да, то
        увеличивает счетчик "пакетов" и начинает передачу. Если нет, то
        остаётся в текущем состоянии ещё на соответствующее время.

        Args:
            sim (Simulator): экземпляр симулятора
            packet (Packet): экземпляр "пакета"
        '''
        if self.code == 0:
            # В начальном состоянии (Arbitrate) создаём новый "пакет"
            packet = Packet(
                present_state=self.code,
                number=self.number
            )
            sim.logger.debug(f'Создан пакет с номером: {self.number}')
            self.number += 1

        if (self.max_transmisions is None or
                sim.context.num_transmissions < self.max_transmisions):
            sim.logger.debug(
                f'Время обработки вышло, отправка пакета № {packet.number}'
            )
            if random.random() > self.probability:
                # Метка осталась в текущем состоянии (неудача)
                self.faild_state_change(sim, packet)
            else:
                # Метка изменила состояние (удача)
                self.success_state_change(sim, packet)
        else:
            sim.logger.info(
                "reached max pings (%d), stopping", self.max_transmisions
            )
            sim.stop()

    def handle_receive(self, sim: Simulator, packet: Packet):
        sim.logger.debug(
            f'Принят пакет № {packet.number} от состояния '
            f'{STATE_CODES_REVERSE[packet.present_state]}'
        )
        sim.logger.info(
            f'Состояние изменено на {STATE_CODES_REVERSE[self.code]}'
        )
        packet.present_state = self.code
        self.num_pakage_sent += 1
        if self.scenario == 3 and self.code == 3:
            sim.context.chunks_passed += 1
        if self.code == 4:
            if self.scenario == 3:
                sim.context.chunks_passed = 0
            sim.context.num_transmissions += 1
            sim.call(sim.context.arbitrate.handle_timeout)
            sim.logger.warning(f'Отправлено заявок: {self.num_pakage_sent}')
        else:
            sim.call(self.handle_timeout, (packet,))

    def calculate_next_state(self, name):
        if name >= 4:
            raise 'Такого состояния не существует!'
        return name + 1

    def __str__(self):
        return f'Состояние метки: {self.code}'
