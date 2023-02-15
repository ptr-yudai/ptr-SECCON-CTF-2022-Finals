FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install curl
WORKDIR /usr/local
RUN curl https://dl.google.com/go/go1.19.5.linux-amd64.tar.gz --output go.tar.gz
RUN rm -rf go && tar -xzf go.tar.gz && rm go.tar.gz
ENV PATH $PATH:/usr/local/go/bin

WORKDIR /tmp
ENTRYPOINT ["go", "build", "-o", "output.bin"]
