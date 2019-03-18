#! /usr/bin/env python3.7
import typing
import socket
import logging
import asyncio
import aioprocessing  # sudo python3.7 -m pip install aioprocessing; # on ImportError

from src import worker
from src import config as conf


class MasterProcess:
    __slots__ = ['workers', 'socket_queue', 'config', 'listen_socket', 'logger', 'time_to_stop']

    def __init__(self, config: conf.Config) -> None:
        self.config = config
        self.socket_queue = aioprocessing.AioQueue()  # конструктор необходимо вызывать внутри asyncio.run()
        self.workers: typing.List[typing.Tuple[aioprocessing.AioQueue, int]] = list()
        self.listen_socket: socket.socket = None
        self.logger = logging  # Пакет-синглтон, используемый как атрибут класса.
        self.logger.root.setLevel(logging.DEBUG)

    async def listen_and_serve(self) -> None:
        """
        Функция, принимающая соединения но одному, отдаёт принятые соединения worker'ам.
        :return:
        """
        while True:  # TODO: придумать корректное завершение всех процессов. (Принципиально ли это в docker?)
            loop = asyncio.get_event_loop()  # текущая запущенная loop
            new_socket: socket.socket;
            host: str;
            port: int
            new_socket, (host, port) = await loop.sock_accept(self.listen_socket)
            self.logger.info(f'New connection accepted from {host}:{port}.')
            await self.socket_queue.coro_put(new_socket)

    async def run(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setblocking(False)
        self.listen_socket.bind(('', self.config.port))
        self.listen_socket.listen(0)

        # запуск worker'ов.
        for worker_id in range(self.config.cpu_limit):
            new_process = aioprocessing.AioProcess(target=worker.new_worker,
                                                   args=(self.socket_queue, worker_id, self.config))
            self.workers.append((new_process, worker_id))
            new_process.start()

        await self.listen_and_serve()  # Принимаем соединения и передаём их worker'ам
        self.listen_socket.close()


def main(debug: typing.Optional[bool]) -> None:
    if debug in [True, None]:
        config_path = "/home/oleg/PyCharmProjects/http-server/httpd.conf"
    else:
        config_path = "/etc/httpd.conf"

    config = conf.Config(config_path)

    if debug is not None:
        config.debug = debug

    if config.debug:
        config.port = 8080
        config.document_root = '/home/oleg/PyCharmProjects/http-server/http-test-suite'

    master = MasterProcess(config)
    print(f'start listen on port {config.port} in {"debug" if config.debug else "realise"} mod.')
    asyncio.run(master.run(), debug=debug)
