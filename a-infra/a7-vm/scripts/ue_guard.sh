#!/bin/bash
# ensure_ue : relance gnb puis ue1 (recréé s'il n'existe plus) tant que l'UE ne répond pas
start_ue() {
  docker rm -f ue1 >/dev/null 2>&1
  docker run -d --name ue1 --network host --privileged \
    -v $HOME/6G/a-infra/a3-core-ran/ran/ue.yaml:/ueransim/config/ue.yaml:ro \
    ueransim:local ./build/nr-ue -c config/ue.yaml >/dev/null
}
ensure_ue() {
  for t in 1 2 3; do
    ip link show uesimtun0 >/dev/null 2>&1 && ping -I uesimtun0 -c1 -W2 -q 192.168.60.20 >/dev/null 2>&1 && return 0
    echo "UE indisponible -> relance gnb puis ue1 (essai $t)" >&2
    docker restart gnb >/dev/null; sleep 4
    if docker inspect ue1 >/dev/null 2>&1; then docker restart ue1 >/dev/null; else start_ue; fi
    sleep 10
  done
  echo "ERREUR : l'UE ne revient pas (voir : docker logs ue1)" >&2; return 1
}
