FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing && apt-get -y upgrade

WORKDIR /app
ADD compare /app
RUN chmod +x /app/compare

ENTRYPOINT ["/app/compare"]
