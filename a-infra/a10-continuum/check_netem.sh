#!/bin/bash
# check_netem.sh : RTT mesuré depuis la VM vers chaque nœud worker (10 pings)
for w in worker worker2 worker3; do
  ip=$(docker inspect -f '{{.NetworkSettings.Networks.kind.IPAddress}}' pf3-$w)
  printf "pf3-%-8s %-12s " $w $ip; ping -c 10 -q $ip | tail -1
done
