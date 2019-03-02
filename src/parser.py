import typing
import socket
import asyncio


class ParserError(Exception):
    pass


# Вычитывает приходящие данные из сокета.
async def __buffer_provider(read_socket: socket.socket):  # -> collections.AsyncGenerator[bytes, None]:
    loop = asyncio.get_event_loop()
    while True:
        buffer = await loop.sock_recv(read_socket, 2024)
        yield buffer


# Обеспечивает равноменый поток байт для парсера, скрывает поступление данных кусками.
async def __byte_provider(read_socket: socket.socket):  # -> collections.AsyncGenerator[int, None]:
    async for buffer in __buffer_provider(read_socket):
        for byte in buffer:
            yield byte


# Парсит поток байт в строки, завершает при нахождении разделителя http-header http-body "\r\n\r\n".
# FIXME: Функция отбрасывает body. (По условию задачи его не болжно быть, но вдруг понадобится.)
async def __lines_provider(read_socket: socket.socket) -> typing.List[bytearray]:
    header_lines: typing.List[bytearray] = []
    current_line = bytearray()
    async for byte in __byte_provider(read_socket):
        if byte == ord('\n'):
            pass
        elif byte == ord('\r'):
            if len(current_line) != 0:
                header_lines.append(current_line)
                current_line = bytearray()
            else:  # если наткнулись на последовательность b"\r\n\r\n":
                return header_lines
        else:
            current_line.append(byte)


matching_hex_characters: typing.Dict[int, int] = {
    ord('0'): 0x0,  # Самый читаемый способ расшифровать hex.
    ord('1'): 0x1,
    ord('2'): 0x2,
    ord('3'): 0x3,
    ord('4'): 0x4,
    ord('5'): 0x5,
    ord('6'): 0x6,
    ord('7'): 0x7,
    ord('8'): 0x8,
    ord('9'): 0x9,
    ord('A'): 0xa,
    ord('B'): 0xb,
    ord('C'): 0xc,
    ord('D'): 0xd,
    ord('E'): 0xe,
    ord('F'): 0xf,
    ord('a'): 0xa,
    ord('b'): 0xb,
    ord('c'): 0xc,
    ord('d'): 0xd,
    ord('e'): 0xe,
    ord('f'): 0xf
}


# Заменяет URL encoding
def unescape_url(url: bytearray) -> str:
    encoded_url = bytearray()
    i = 0
    while i < len(url):
        if url[i] == ord(b'%'):
            first_octet = matching_hex_characters[url[i + 1]] << 4
            second_octet = matching_hex_characters[url[i + 2]]
            encoded_url.append(first_octet + second_octet)
            i += 3
        else:
            encoded_url.append(url[i])
            i += 1
    encoded_url = encoded_url.decode(encoding="utf-8")
    return encoded_url


# парсит первую строку header:
# 'GET /robots.txt HTTP/1.1' --> {'Method': 'GET', 'Domain':'/robots.txt', 'Protocol': 'HTTP/1.1'}
def __first_line_parser(line: bytearray):
    method, domain, protocol = line.split(sep=b' ')
    method = method.decode(encoding="utf-8")
    domain = unescape_url(domain)
    protocol = protocol.decode(encoding="utf-8")
    return {'Method': method, 'Domain': domain, 'Protocol': protocol}


# парсит header ключ/значение.
# ['Accept: image/webp,*/*'] --> {'Accept': 'image/webp,*/*'}
def __key_value_line_parser(header_lines: typing.List[bytearray]):
    result: typing.Dict[str, str] = dict()
    for line in header_lines:
        k, v = line.split(sep=b': ')
        result[k.decode(encoding="utf-8")] = v.decode(encoding='utf-8')
    return result


headers = typing.Dict[str, str]


# парсит header часть http запроса.
# 'GET /favicon.ico HTTP/1.1\r\n'\
# 'User-Agent: Mozilla/5.0'\r\n'\
# '\r\n'
# {
#     'Method': 'GET',
#     'Domain': '/favicon.ico',
#     'Protocol': 'HTTP/1.1',
#     'User-Agent': 'Mozilla/5.0'
# }
async def parser(read_socket: socket.socket) -> typing.Dict[str, str]:
    # TODO: Понять, какие возможны ошибки и перехватывать их.
    header_lines = await __lines_provider(read_socket)
    header = __first_line_parser(header_lines[0])
    header.update(__key_value_line_parser(header_lines[1:-1]))
    return header
