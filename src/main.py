import argparse
import typing
import multiprocessing
import socket

import src.config as conf
from src.worker import Worker

QUEUE_SIZE = 8


def parse_args() -> typing.Dict[str, typing.Any]:
    parser = argparse.ArgumentParser(description='Web-server for highload tp course')
    parser.add_argument('--config-file', type=str, help='file to load parameters for run server')
    parser.add_argument('--host', type=str, default='localhost', help='address to bind server socket')
    parser.add_argument('--port', type=int, default=80, help='port to bind server socket')
    parser.add_argument('--cpu_limit', type=int, default=1, help='number of workers to run by server')
    parser.add_argument('--document_root', type=str, help='absolute path to serve files from')
    return dict(vars(parser.parse_args()))


def main() -> None:
    namespase = parse_args()
    config = conf.Config(namespase.get('config_file', '/etc/httpd.conf'))
    if namespase['host']:
        config.host = namespase['host']
    if namespase['port']:
        config.port = namespase['port']
    if namespase['cpu_limit']:
        config.cpu_limit = namespase['cpu_limit']
    if namespase['document_root']:
        config.document_root = namespase['document_root']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((config.host, config.port))
    sock.listen(QUEUE_SIZE)
    sock.setblocking(False)

    workers: typing.List[multiprocessing.Process] = []

    for _ in range(config.cpu_limit):

        worker = Worker(sock, config)
        worker_process = multiprocessing.Process(target=worker.run)
        workers.append(worker_process)
        worker_process.start()

    try:
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        for worker in workers:
            worker.terminate()

    print('Server terminated.')


if __name__ == '__main__':
    main()
