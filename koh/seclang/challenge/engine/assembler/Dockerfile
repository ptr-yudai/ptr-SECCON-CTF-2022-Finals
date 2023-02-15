FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y binutils nasm

RUN mkdir /app
ADD assemble /app
RUN chmod +x /app/assemble

WORKDIR /app
ENTRYPOINT ["/app/assemble"]
