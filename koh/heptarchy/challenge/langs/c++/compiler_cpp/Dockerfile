FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y g++

WORKDIR /tmp
ENTRYPOINT ["g++", "-o", "output.bin"]
