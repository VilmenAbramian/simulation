from dataclasses import dataclass
import random
from typing import Optional

from pysim.sim.logger import ModelLogger
from .objects import Config
from pysim.sim import Simulator


class Model:
    def __init__(self, config: Config, logger: ModelLogger):
        self.config = config
        self.channel = Channel(
            delay=config.channel_delay,
        )
        self.client = Client(
            interval=self.config.interval,
            max_pings=config.max_pings,
        )
        self.server = Server(
            loss_prob=self.config.loss_prob,
            delay=self.config.service_delay,
        )

        # Связываем взаимодействующие компоненты
        self.client.set_server(self.server)
        self.client.set_channel(self.channel)
        self.server.set_channel(self.channel)

        # Делаем запись в журнал
        logger.debug("Model was successfully initialized")


class Node:
    """
    Базовый класс для клиента и сервера, интерфейс для канала.
    """
    def handle_receive(self, sim: Simulator, pkt: "Packet"):
        raise NotImplementedError


@dataclass
class Packet:
    sender: Node
    receiver: Node
    number: int


class Client(Node):
    """
    Модель отправителя.
    """
    def __init__(
        self,
        interval: float,
        max_pings: int | None
    ):
        self.interval = interval
        self.max_pings = max_pings

        # Connections:
        self._server: Server | None = None
        self._channel: Channel | None = None

        # State:
        self.number: int = random.randint(a=0, b=1_000_000)
        self.was_acknowledged: bool = False

        # Statistics:
        self.num_pings_sent = 0
        self.num_acknowledged = 0
        self.num_missed = 0
        self.num_bad_pongs = 0
        self.intervals_list = []

    def set_server(self, server: "Server"):
        self._server = server

    @property
    def server(self) -> Optional["Server"]:
        return self._server

    def set_channel(self, channel: "Channel"):
        self._channel = channel

    @property
    def channel(self) -> Optional["Channel"]:
        return self._channel

    def handle_timeout(self, sim: Simulator) -> None:
        """
        При достижении таймаута отправитель рассчитывает, получил ли он
        Pong, увеличивает счетчик пакетов и начинает передачу.

        Args:
            sim (Simulator): экземпляр симулятора
        """
        assert self.channel is not None
        assert self.server is not None

        if not self.was_acknowledged:
            self.num_missed += 1
        self.number += 1
        if self.max_pings is None or self.num_pings_sent < self.max_pings:
            sim.logger.debug("client timeout, sending ping #%d", self.number)
            packet = Packet(
                sender=self,
                receiver=self.server,
                number=self.number
            )
            sim.call(self.channel.send, (packet,))
            self.num_pings_sent += 1
        else:
            # Если достигли максимального числа пингов, останавливаемся.
            sim.logger.info("reached max pings (%d), stopping", self.max_pings)
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

    def __str__(self):
        return "client"


class Server(Node):
    def __init__(self, loss_prob: float, delay: float):
        self.loss_prob = loss_prob
        self.delay = delay
        self._channel: "Channel" | None = None

    def set_channel(self, channel: "Channel") -> None:
        self._channel = channel

    @property
    def channel(self) -> Optional["Channel"]:
        return self._channel

    def handle_receive(self, sim: Simulator, ping: Packet) -> None:
        """
        Обработка события получения Ping-а.

        Разыгрываем случайное число, с вероятностью (1 - loss_prob) имитируем
        задержку обработки (delay) и отправляем Pong. С вероятностью loss_prob
        теряем пакет.

        Args:
            sim (Simulator): симулятор
            ping (Packet): число из Ping-а
        """
        if random.random() > self.loss_prob:
            # Пакет не потерян (1 >= X > Pl <=> 0 <= X < 1 - Pl)
            sim.logger.debug("ping successfully reached the server")
            sim.schedule(self.delay, self.handle_service_end, (ping,))
        else:
            # Если тут - пакет потерян
            sim.logger.debug("ping lost on channel")
            sim.schedule(
                sim.context.client.interval,
                sim.context.client.handle_timeout
            )

    def handle_service_end(self, sim: Simulator, ping: Packet) -> None:
        """
        Обработка события окончания обработки пакета Ping{number}.
        Отправляем Pong{number} в канал.

        Args:
            sim (Simulator): симулятор
            ping (Packet): число из Ping-а
        """
        assert self.channel is not None

        pong = Packet(
            sender=self,
            receiver=ping.sender,
            number=ping.number
        )
        sim.logger.debug("server sent pong")
        sim.call(self.channel.send, (pong,), msg=f"sending Pong#{pong.number}")

    def __str__(self):
        return "server"


class Channel:
    def __init__(self, delay: float):
        self.delay = delay
        self.delays_list = []

    def send(self, sim: Simulator, packet: Packet):
        sim.logger.debug("packet travel through the channel")
        sim.schedule(
            self.delay,
            packet.receiver.handle_receive,
            (packet,),
            msg=f"{packet.sender} --({packet.number})--> {packet.receiver}"
        )
        self.delays_list.append(self.delay)

    def __str__(self):
        return "Channel"
