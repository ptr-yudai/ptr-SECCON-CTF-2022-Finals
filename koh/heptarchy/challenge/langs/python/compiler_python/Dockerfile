FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install \
    build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev wget

ARG UID=1000
ARG GID=1000
RUN useradd -u $UID -o -m user
RUN groupmod -g $GID -o user

WORKDIR /home/user
USER user
ADD 3.12.0a3 .
ENV PATH $PATH:/home/user/bin
ENV LD_LIBRARY_PATH /home/user/lib

WORKDIR /tmp
ENTRYPOINT ["python3.12", "-m", "compileall"]
