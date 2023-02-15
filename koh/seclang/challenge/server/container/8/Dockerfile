FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -y update --fix-missing && apt-get -y upgrade
RUN apt-get install -y python3 python3-pip
RUN pip3 install lark

# This is the directory you can upload.
# The directory must contain at least two files: "init.sh" and "entry.sh"
# - init.sh: Initialization script for docker build
# - entry.sh: Entrypoint script for docker run
ADD ./container/ /app
RUN chmod +x /app/init.sh
RUN chmod +x /app/entry.sh
WORKDIR /app

RUN /app/init.sh
ENTRYPOINT ["/app/entry.sh"]
