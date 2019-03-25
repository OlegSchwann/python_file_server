import asyncio
import socket
import uvloop
import src.http_parser as http_parser
import src.http_response_builder as http_response_builder

import src.config as conf

_CHUNK_SIZE = 262144

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Worker:
    __slots__ = ['listen_socket', 'config', 'loop']

    def __init__(self, listen_socket: socket.socket, config: conf.Config) -> None:
        self.listen_socket = listen_socket
        self.config = config
        self.loop = uvloop.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self) -> None:
        self.loop.run_until_complete(self._run_worker())

    async def _run_worker(self):
        while True:
            conn, _ = await self.loop.sock_accept(self.listen_socket)
            conn.settimeout(5)
            self.loop.create_task(self.handle_connection(conn))

    async def handle_connection(self, handle_socket: socket.socket) -> None:
        # потоковое чтение запроса из сокета
        try:
            request_headers = await http_parser.parser(handle_socket)
        except http_parser.ConnectionLost:
            pass
        else:
            await http_response_builder.serve_request(request_headers, handle_socket, self.config)
        handle_socket.close()
