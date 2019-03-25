FROM python:3.7

RUN apt-get update
RUN pip install uvloop

COPY ./src /bin/highload-server/src
 
EXPOSE 80

WORKDIR /bin/highload-server

ENV PYTHONPATH=/bin/highload-server
CMD python3.7 ./src/main.py --config-file /etc/httpd.conf
