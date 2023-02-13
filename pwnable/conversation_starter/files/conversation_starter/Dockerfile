FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install xinetd
RUN groupadd -r pwn && useradd -r -g pwn pwn

ADD etc/pwn.xinetd /etc/xinetd.d/pwn
ADD etc/init.sh    /etc/init.sh
ADD etc/redir.sh   /home/pwn/.redir.sh
RUN chmod 550 /home/pwn/.redir.sh
RUN chmod 700 /etc/init.sh
RUN chmod 1733 /tmp /var/tmp /dev/shm
RUN echo "FAKECON{*** REDACTED ***}" > /flag.txt
RUN chmod 444 flag.txt

WORKDIR /home/pwn
ADD bin/chall chall
RUN chmod 550 chall

RUN chown -R root:pwn /home/pwn

RUN ls /home/pwn -lh

RUN service xinetd restart
