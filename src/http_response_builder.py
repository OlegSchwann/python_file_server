# Пакет содержит логику создания http ответов.

import datetime
import os
import typing
import mimetypes
import socket
import asyncio

from src import http_parser as parser
from src import search_file
from src import config as conf


class ResponseHeaders:
    def __init__(self):
        self.protocol: str = 'HTTP/1.1'
        self.status_code: str = '200 OK'
        self.headers: typing.Dict[str, str] = {
            # Рабочее имя сервера
            'Server': '\U0001f40d',
            # дата в формате https://tools.ietf.org/html/rfc7231#section-7.1.1.1
            'Date': datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            'Connection': 'close'
        }
        # Use ResponseHeaders.update as dict.update .
        self.update = self.headers.update

    def __str__(self) -> str:
        return f'{self.protocol} {self.status_code}\r\n' + \
               '\r\n'.join([f'{k}: {v}' for k, v in self.headers.items()]) + \
               '\r\n\r\n'


# Преобразует расширение файла в mime_type: '/index.html'-> 'text/html'.
def get_content_type(url: str) -> str:
    mime_type, encoding = mimetypes.guess_type(url)
    return (mime_type + (f"; charset={encoding}" if encoding else "")) or 'application/octet-stream'


# --------------------------------------------------------------------------------
# Полностью обслуживает запрос, отправляет нужные данные, не закрывает сокет.
async def serve_request(request_headers: parser.headers, connection: socket.socket, config: conf.Config) -> None:
    try:
        if request_headers['Method'] == 'GET':
            await serve_get_request(request_headers, connection, config)
        elif request_headers['Method'] == 'HEAD':
            await serve_head_request(request_headers, connection, config)
        else:
            await serve_method_not_allowed_request(request_headers, connection, config)
    except FileNotFoundError:
        if not request_headers['Domain'].endswith(search_file.DEFAULT_FILE_IN_FOLDER):
            await serve_not_found_request(request_headers, connection, config)
        else:
            await serve_forbidden_request(request_headers, connection, config)
    except PermissionError:
        await serve_forbidden_request(request_headers, connection, config)
    except NotADirectoryError:
        await serve_not_found_request(request_headers, connection, config)


async def serve_head_request(request_headers: parser.headers, connection: socket.socket, config: conf.Config) -> None:
    headers = ResponseHeaders()
    request_headers['Domain'], _ = search_file.path_converter(request_headers['Domain'], config.document_root)

    headers.update({
        'Content-Type': get_content_type(request_headers['Domain']),
        'Content-Length': os.path.getsize(request_headers['Domain']),
    })

    loop = asyncio.get_event_loop()
    await loop.sock_sendall(connection, data=bytes(str(headers), encoding='utf-8'))


async def serve_get_request(request_headers: parser.headers, served_socket: socket.socket, config: conf.Config) -> None:
    headers = ResponseHeaders()
    request_headers['Domain'], _ = search_file.path_converter(request_headers['Domain'], config.document_root)
    with open(request_headers['Domain'], mode='rb') as target_file:
        headers.update({
            'Content-Type': get_content_type(request_headers['Domain']),
            'Content-Length': os.path.getsize(target_file.fileno()),
        })
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(served_socket, data=bytes(str(headers), encoding='utf-8'))
        # Едиственный пример использования sock_sendfile есть в тестах интерпретатора:
        # https://github.com/python/cpython/commit/6b5a27975a415108a5eac12ee302bf2b3233f4d4
        # Это обёртка вокруг системного вызова, возлагающего все заботы на OS: $ man 2 sendfile;
        await loop.sock_sendfile(sock=served_socket, file=target_file)


async def serve_method_not_allowed_request(request_headers: parser.headers, connection: socket.socket,
                                           config: conf.Config) -> None:
    headers = ResponseHeaders()
    headers.status_code = '405 Not Allowed'
    headers.update({
        'Content-Type': 'text/html; charset=UTF-8',
        'Content-Length': 0,
    })
    loop = asyncio.get_event_loop()
    await loop.sock_sendall(connection, data=bytes(str(headers), encoding='utf-8'))


async def serve_forbidden_request(request_headers: parser.headers, connection: socket.socket,
                                  config: conf.Config) -> None:
    headers = ResponseHeaders()
    headers.status_code = '403 Forbidden'
    headers.update({
        'Content-Type': 'text/html; charset=UTF-8',
        'Content-Length': 0,
    })
    loop = asyncio.get_event_loop()
    await loop.sock_sendall(connection, data=bytes(str(headers), encoding='utf-8'))


async def serve_not_found_request(request_headers: parser.headers, connection: socket.socket,
                                  config: conf.Config) -> None:
    headers = ResponseHeaders()
    headers.status_code = '404 Not Found'
    headers.update({
        'Content-Type': 'text/html; charset=UTF-8',
        'Content-Length': 0,
    })
    loop = asyncio.get_event_loop()
    await loop.sock_sendall(connection, data=bytes(str(headers), encoding='utf-8'))
