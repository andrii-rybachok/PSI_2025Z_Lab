FROM debian:stable-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server.c /app/server.c

RUN gcc -Wall -Wextra -O2 server.c -o server -lssl -lcrypto

EXPOSE 9000/udp

CMD ["./server", "9000"]
