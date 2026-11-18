#!/bin/bash
# swap_ran.sh <image> : (re)crée gnb puis ue1 avec l'image donnée, et vérifie la connectivité
IMG=${1:-ueransim:local}
cd "$(dirname "$0")"
docker rm -f ue1 gnb >/dev/null 2>&1
docker run -d --name gnb --network host --restart unless-stopped \
  -v $PWD/gnb.yaml:/ueransim/config/gnb.yaml:ro $IMG ./build/nr-gnb -c config/gnb.yaml >/dev/null
sleep 4
docker run -d --name ue1 --network host --privileged \
  -v $PWD/ue.yaml:/ueransim/config/ue.yaml:ro $IMG ./build/nr-ue -c config/ue.yaml >/dev/null
sleep 10
echo "image : $(docker inspect ue1 --format '{{.Config.Image}}')"
docker logs gnb 2>&1 | grep -i 'NG Setup' | tail -1
docker logs ue1 2>&1 | grep -E 'Registration is successful|PDU Session establishment is successful|TUN interface'
ping -I uesimtun0 -c3 192.168.60.20
