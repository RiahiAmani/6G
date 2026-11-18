#!/bin/bash
# netem.sh apply|clear|status : latence (tc netem) et capacité (docker update) des trois tiers
# À relancer après un redémarrage de la VM : les règles tc ne survivent pas.
N=pf3
case $1 in
apply)
  docker exec ${N}-worker  tc qdisc replace dev eth0 root netem delay 2ms  1ms || exit 1
  docker exec ${N}-worker2 tc qdisc replace dev eth0 root netem delay 10ms 2ms || exit 1
  docker exec ${N}-worker3 tc qdisc replace dev eth0 root netem delay 40ms 5ms || exit 1
  docker update --cpus=1 --memory=1g    --memory-swap=1g    ${N}-worker  >/dev/null   # Edge : petit
  docker update --cpus=2 --memory=1500m --memory-swap=1500m ${N}-worker2 >/dev/null   # Fog
  docker update --cpus=3 --memory=2g    --memory-swap=2g    ${N}-worker3 >/dev/null   # Cloud : grand
  ;;
clear)   # supprime la latence seulement (les limites de CPU/RAM restent)
  for w in worker worker2 worker3; do docker exec ${N}-$w tc qdisc del dev eth0 root 2>/dev/null; done ;;
status) ;;
*) echo "usage : $0 apply|clear|status"; exit 1 ;;
esac
for w in worker worker2 worker3; do
  echo "== ${N}-$w : $(docker exec ${N}-$w tc qdisc show dev eth0 | head -1)"
  docker inspect ${N}-$w --format '     CPU max = {{.HostConfig.NanoCpus}} nanoCPU   RAM max = {{.HostConfig.Memory}} octets'
done
