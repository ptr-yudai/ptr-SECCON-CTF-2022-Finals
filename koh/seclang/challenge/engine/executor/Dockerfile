FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y libseccomp2

WORKDIR /app
ADD sandbox /app
RUN chmod +x /app/sandbox
