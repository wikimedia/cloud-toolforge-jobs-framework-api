FROM debian:buster-slim
WORKDIR /app
RUN apt-get update
RUN apt-get install uwsgi-plugin-python3 python3-pip python3-wheel python3-setuptools -y --no-install-recommends
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "uwsgi", "--socket", "127.0.0.1:8000", \
               "--plugin", "python3", \
               "--mount", "/=api:app", \
               "--master" ]
