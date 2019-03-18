FROM python:3.7.2-alpine3.9


# real libraries
COPY ./requirements.txt /usr/local/python/http-server/
RUN ["/usr/local/bin/pip", "install", "--requirement", "/usr/local/python/http-server/requirements.txt"]

# Исходный код проекта.
COPY ./main.py /usr/local/python/http-server/
COPY ./src /usr/local/python/http-server/src

# Порт, на котором слушает сервер.
EXPOSE 80

# Место расположение конфига и папки со статикой.
VOLUME ["/etc/httpd.conf", "/var/www/html"]

WORKDIR "/usr/local/python/http-server"

CMD ["/usr/local/bin/python3", "./main.py", "--release"]
