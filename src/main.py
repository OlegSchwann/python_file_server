#! /usr/bin/env python3.7
import random
import typing
import configparser
from io import StringIO
import os
import socket
import dataclasses
import logging
import aioprocessing  # sudo python3.7 -m pip install aioprocessing; # https://github.com/dano/aioprocessing
import asyncio

import worker


# пример для ускорения. https://github.com/jpyatachkov/ssanic

# открываем сокет
# Запуск асинхронных workers.
# модули: парсинг запроса
# записывание файла

@dataclasses.dataclass
class Config:
    cpu_limit: int  # maximum CPU count to use for non-blocking servers
    document_root: str  # folder for site root
    port: int  # listen tcp port


class MasterProcess:
    __slots__ = ['workers', 'socket_queue', 'config', 'listen_socket', 'logger', 'time_to_stop']

    def __init__(self, config: Config) -> None:
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
        while True:  # TODO: придумать корректное завершение.
            loop = asyncio.get_event_loop()  # текущая запущенная loop
            new_socket: socket.socket; host: str; port: int
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
            new_process = aioprocessing.AioProcess(target=worker.new_worker, args=(self.socket_queue, worker_id))
            self.workers.append((new_process, worker_id))
            new_process.start()

        await self.listen_and_serve()  # Принимаем соединения и передаём их worker'ам
        self.listen_socket.close()


def parse_config(config_path: str = '/etc/httpd.conf') -> Config:
    with StringIO() as fullConfig, open(config_path) as realConfig:
        fullConfig.write('[main_section]\n')
        fullConfig.write(realConfig.read())
        fullConfig.seek(0, os.SEEK_SET)
        parsed_config = configparser.ConfigParser(
            defaults={
                "cpu_limit": "4",  # maximum CPU count to use for non-blocking servers
                "document_root": "/var/www/html",
                "port": str(random.randint(2000, 4000))  # TODO: по условиям сборки порт по умолчанию 80.
            },
            comment_prefixes=('#',),
            delimiters=(' ',),
            inline_comment_prefixes=('#',))
        parsed_config.read_file(fullConfig)
    cpu_limit = parsed_config.getint("main_section", "cpu_limit")
    document_root = parsed_config.get("main_section", "document_root")
    port = parsed_config.getint("main_section", "port")
    return Config(cpu_limit=cpu_limit, document_root=document_root, port=port)


async def main() -> None:
    config = parse_config("/home/oleg/PyCharmProjects/http-server/httpd.conf")
    master = MasterProcess(config)
    print("start listen on port", config.port)
    await master.run()


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
