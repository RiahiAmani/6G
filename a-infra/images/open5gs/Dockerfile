FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends software-properties-common gnupg \
      ca-certificates iproute2 iputils-ping tcpdump \
 && add-apt-repository -y ppa:open5gs/latest \
 && apt-get update && apt-get install -y open5gs \
 && rm -rf /var/lib/apt/lists/*
