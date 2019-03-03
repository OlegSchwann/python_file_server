FROM python:3.7.2-alpine3.9

MAINTAINER OlegSchwann

# Статика для тестирования.
COPY ./http-test-suite/httptest /var/www/html/httptest

# Зависимости проекта
COPY ./requirements.txt /usr/local/python/http-server/
RUN pip install --requirement '/usr/local/python/http-server/requirements.txt'

# Исходный код проекта
COPY ./main.py /usr/local/python/http-server/
COPY ./src /usr/local/python/http-server/src
COPY ./httpd.conf /etc/httpd.conf

# Порт, на котором слушает сервер.
EXPOSE 80/tcp

WORKDIR '/usr/local/python/http-server'

CMD ["/usr/local/bin/python3", "./main.py", "--release"]
