FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y python3 python3-pip socat
RUN pip3 install lark

ADD ./container/ /app

WORKDIR /app
ENTRYPOINT ["socat", "TCP-L:9999,fork,reuseaddr", "EXEC:'python3 seclang.py',stderr"]
