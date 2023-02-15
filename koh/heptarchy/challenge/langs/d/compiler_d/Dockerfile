FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install curl gcc
RUN curl https://downloads.dlang.org/releases/2.x/2.101.2/dmd_2.101.2-0_amd64.deb --output dmd.deb
RUN dpkg -i dmd.deb && rm dmd.deb

WORKDIR /tmp
ENTRYPOINT ["dmd", "-of=output.bin"]
