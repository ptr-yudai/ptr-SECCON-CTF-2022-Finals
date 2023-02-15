FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y gcc

WORKDIR /tmp
ENTRYPOINT ["gcc", "-o", "output.bin"]
