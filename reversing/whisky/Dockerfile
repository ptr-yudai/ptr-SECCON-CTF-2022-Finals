FROM python:3.11-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN groupadd -r ctf && useradd -r -g ctf ctf
RUN apt-get -y install gcc libssl-dev
RUN pip install uwsgi

WORKDIR /app
ADD build/server/uwsgi.ini   /app
ADD files/backdoor_plugin.so /app
RUN chown root:ctf -R /app
RUN chmod 444 uwsgi.ini
RUN chmod 555 backdoor_plugin.so

ADD build/flag.txt /
RUN chown root:root /flag.txt
RUN chmod 444 /flag.txt

USER ctf
ENTRYPOINT ["uwsgi", "--ini", "uwsgi.ini"]
