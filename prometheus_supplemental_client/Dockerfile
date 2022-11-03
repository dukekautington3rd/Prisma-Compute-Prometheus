FROM --platform=amd64 python:3.11-alpine
USER nobody
LABEL MAINTAINER="lonkaut@gmail.com"

RUN python3 -m venv /tmp/prometheus_client/venv

COPY requirements.txt /tmp/prometheus_client/
RUN . /tmp/prometheus_client/venv/bin/activate && pip install -r /tmp/prometheus_client/requirements.txt

COPY main.py /tmp/prometheus_client/

CMD . /tmp/prometheus_client/venv/bin/activate && exec python3 -u /tmp/prometheus_client/main.py