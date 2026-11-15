#!/bin/bash
# core-net.sh : à lancer (sudo) sur la VM qui héberge l'UPF
set -e
sysctl -w net.ipv4.ip_forward=1 >/dev/null
ip tuntap add name ogstun mode tun 2>/dev/null || true
ip addr replace 10.45.0.1/16 dev ogstun
ip link set ogstun up
iptables -t nat -C POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE 2>/dev/null || \
  iptables -t nat -A POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE
iptables -C FORWARD -s 10.45.0.0/16 -j ACCEPT 2>/dev/null || iptables -I FORWARD -s 10.45.0.0/16 -j ACCEPT
iptables -C FORWARD -d 10.45.0.0/16 -j ACCEPT 2>/dev/null || iptables -I FORWARD -d 10.45.0.0/16 -j ACCEPT
echo "core-net OK"
