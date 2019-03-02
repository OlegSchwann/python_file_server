# https://steelkiwi.com/blog/working-tcp-sockets/

import asyncio
import socket
import logging
import aioprocessing  # sudo python3.7 -m pip install aioprocessing; # https://github.com/dano/aioprocessing

from src import parser


def new_worker(connection_source: aioprocessing.AioQueue, worker_id: int):
    """
    Фабричная функция для запуска Worker в новом потоке.
    """
    worker = Worker(connection_source, worker_id)
    asyncio.run(worker.listen_and_serve(), debug=True)


class Worker:
    __slots__ = ['connection_source', 'worker_id', 'logger']

    def __init__(self, connection_source: aioprocessing.AioQueue, worker_id: int):
        self.connection_source = connection_source
        self.worker_id = worker_id
        self.logger = logging

    async def serve_connection(self, served_socket: socket.socket) -> None:
        # потоковое чтение запроса из сокета
        print(await parser.parser(served_socket))

        # await self.loop.sock_recv(served_socket, nbytes=2048)
        head = b"HTTP/1.1 200 OK\r\n" \
               b"Content-Type: text/plain; charset=utf-8\r\n" \
               b"\r\n"
        await asyncio.get_event_loop().sock_sendall(served_socket, data=head)
        with open("/home/oleg/PyCharmProjects/http-server/worker.py", mode='rb') as file:
            loop = asyncio.get_event_loop()
            # Едиственный пример использования sock_sendfile есть в тестах интерпретатора:
            # https://github.com/python/cpython/commit/6b5a27975a415108a5eac12ee302bf2b3233f4d4
            # Это обёртка вокруг системного вызова, возлагающего все заботы на OS: $ man 2 sendfile;
            await loop.sock_sendfile(sock=served_socket, file=file)
        served_socket.shutdown(socket.SHUT_RDWR)  # Закрытие tcp соединения, а не файлового дескриптора.
        served_socket.close()

    async def listen_and_serve(self):
        while True:
            new_socket: socket.socket = await self.connection_source.coro_get()
            new_socket.setblocking(False)
            await asyncio.get_event_loop().create_task(self.serve_connection(new_socket))
