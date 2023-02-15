FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install python3 git xz-utils bzip2

WORKDIR /root
RUN git clone https://github.com/emscripten-core/emsdk.git
WORKDIR /root/emsdk
RUN ./emsdk install latest
RUN ./emsdk activate latest
ENV PATH $PATH:/root/emsdk/upstream/emscripten

WORKDIR /tmp
ENTRYPOINT ["emcc", "-O1", "-o", "mission-7.js"]
