#!/bin/bash
# recover.sh ue|host [ip] : durée d'une panne (détection -> retour du service)
#  ue   : ping UE -> vm-k8s ; sans reprise en 30 s, l'UE est relancé (nouvelle session PDU)
#  host : ping direct d'une VM (par défaut vm-upf) = durée d'indisponibilité de la VM
export LC_ALL=C
MODE=${1:-ue}; IP=${2:-192.168.60.11}
if [ "$MODE" = ue ]; then P="ping -I uesimtun0 -c1 -W1 192.168.60.20"; else P="ping -c1 -W1 $IP"; fi
now() { date +%s.%N; }
echo "attente de la panne..."
while true; do T=$(now); if ! $P >/dev/null 2>&1; then T0=$T; break; fi; sleep 0.2; done
echo "panne détectée à $(date +%T)"
RESTARTED=non
while ! $P >/dev/null 2>&1; do
  if [ "$MODE" = ue ] && [ $RESTARTED = non ] && awk -v a=$T0 -v b=$(now) 'BEGIN{exit !(b-a>30)}'; then
    echo "pas de reprise automatique en 30 s -> docker restart ue1"
    docker restart ue1 >/dev/null; RESTARTED=oui; sleep 6
  fi
  sleep 0.2
done
awk -v a=$T0 -v b=$(now) -v r=$RESTARTED 'BEGIN{printf "service rétabli après %.1f s (relance UE : %s)\n", b-a, r}'
