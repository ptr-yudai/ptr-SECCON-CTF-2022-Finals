FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y python3 python3-pip
RUN pip3 install lark

ADD . /app

WORKDIR /app
ENTRYPOINT ["python3", "seclang.py"]
