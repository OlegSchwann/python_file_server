import configparser
import os
from io import StringIO


class Config:
    __slots__ = [
        'cpu_limit',  # Maximum CPU count to use for non-blocking servers. Default 4.
        'document_root',  # Folder for site root.                              Default "/var/www/html".
        'port',  # Listen tcp port.                                   Default 80.
        'debug'  # Is debug configuration.                            Default True.
    ]

    def __init__(self, path: str = '/etc/httpd.conf'):
        with StringIO() as fullConfig, open(path) as realConfig:
            fullConfig.write('[main_section]\n')
            fullConfig.write(realConfig.read())
            fullConfig.seek(0, os.SEEK_SET)
            parsed_config = configparser.ConfigParser(
                defaults={
                    "cpu_limit": "4",
                    "document_root": "/var/www/html",
                    "port": "80",
                    "debug": True
                },
                comment_prefixes=('#',),
                delimiters=(' ',),
                inline_comment_prefixes=('#',))
            parsed_config.read_file(fullConfig)
        self.cpu_limit = parsed_config.getint("main_section", "cpu_limit")
        self.document_root = parsed_config.get("main_section", "document_root")
        self.port = parsed_config.getint("main_section", "port")
        self.debug = parsed_config.getboolean("main_section", "debug")
