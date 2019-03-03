# https://steelkiwi.com/blog/working-tcp-sockets/

import asyncio
import socket
import logging
import aioprocessing  # sudo python3.7 -m pip install aioprocessing; # https://github.com/dano/aioprocessing

from src import config as conf
from src import http_parser
from src import http_response_builder



def new_worker(connection_source: aioprocessing.AioQueue, worker_id: int, config: conf.Config):
    """
    Фабричная функция для запуска Worker в новом потоке.
    """
    worker = Worker(connection_source, worker_id, config)
    asyncio.run(worker.listen_and_serve(), debug=True)


class Worker:
    __slots__ = ['connection_source', 'worker_id', 'logger', 'config']

    def __init__(self, connection_source: aioprocessing.AioQueue, worker_id: int, config: conf.Config):
        self.connection_source = connection_source
        self.worker_id = worker_id
        self.logger = logging
        self.config = config

    async def serve_connection(self, served_socket: socket.socket) -> None:
        # потоковое чтение запроса из сокета
        try:
            request_headers = await http_parser.parser(served_socket)
        except http_parser.ConnectionLost:
            pass
        else:
            await http_response_builder.serve_request(request_headers, served_socket, self.config)
            served_socket.shutdown(socket.SHUT_RDWR)  # Закрытие tcp соединения, а не файлового дескриптора.
        served_socket.close()  # Закрытие файлового дескриптора.

    async def listen_and_serve(self):
        while True:
            new_socket: socket.socket = await self.connection_source.coro_get()
            new_socket.setblocking(False)
            await asyncio.get_event_loop().create_task(self.serve_connection(new_socket))
