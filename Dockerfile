FROM docker-registry.wikimedia.org/python3-bullseye:latest

RUN mkdir -pv /run/prometheus-multiproc
ENV PROMETHEUS_MULTIPROC_DIR /run/prometheus-multiproc

WORKDIR /app
RUN apt-get update
RUN apt-get install uwsgi-plugin-python3 -y --no-install-recommends
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "uwsgi", "--socket", "127.0.0.1:8000", \
               "--plugin", "python3", \
               "--mount", "/=api:app", \
               "--master" ]
