FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install xinetd
RUN groupadd -r pwn && useradd -r -g pwn pwn

ADD files/conversation_starter/etc/pwn.xinetd /etc/xinetd.d/pwn
ADD files/conversation_starter/etc/init.sh    /etc/init.sh
ADD files/conversation_starter/etc/redir.sh   /home/pwn/.redir.sh
RUN chmod 550 /home/pwn/.redir.sh
RUN chmod 700 /etc/init.sh
RUN chmod 1733 /tmp /var/tmp /dev/shm
ADD builds/flag.txt /flag.txt
RUN chmod 444 flag.txt

WORKDIR /home/pwn
ADD files/conversation_starter/bin/chall chall
RUN chmod 550 chall

RUN chown -R root:pwn /home/pwn

RUN ls /home/pwn -lh

RUN service xinetd restart
