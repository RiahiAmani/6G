FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git make gcc g++ cmake libsctp-dev \
      lksctp-tools iproute2 iputils-ping iperf3 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/aligungr/UERANSIM /ueransim && cd /ueransim && make -j2
WORKDIR /ueransim
