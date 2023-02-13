FROM ubuntu:22.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get -y install xinetd
RUN groupadd -r pwn && useradd -r -g pwn pwn

ADD files/diagemu/etc/pwn.xinetd /etc/xinetd.d/pwn
ADD files/diagemu/etc/init.sh    /etc/init.sh
ADD files/diagemu/etc/redir.sh   /home/pwn/.redir.sh
ADD files/diagemu/bin/libunicorn.so.2 /usr/lib/x86_64-linux-gnu/libunicorn.so.2
RUN chmod 550 /home/pwn/.redir.sh
RUN chmod 700 /etc/init.sh
RUN chmod 644 /usr/lib/x86_64-linux-gnu/libunicorn.so.2
RUN chmod 1733 /tmp /var/tmp /dev/shm

WORKDIR /home/pwn
ADD build/flag.txt  flag.txt
ADD files/diagemu/bin/diagemu diagemu
RUN chmod 440 flag.txt
RUN chmod 550 diagemu
RUN mv flag.txt flag-$(md5sum flag.txt | awk '{print $1}').txt

RUN chown -R root:pwn /home/pwn
RUN ls /home/pwn -lh
RUN service xinetd restart
