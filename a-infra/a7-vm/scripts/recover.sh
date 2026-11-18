#!/bin/bash
# recover.sh <ue|host> [ip] [attente_max_s] : durée d'une panne (détection -> retour du service)
export LC_ALL=C
MODE=${1:-ue}; IP=${2:-192.168.60.11}; WAIT=${3:-30}
if [ "$MODE" = ue ]; then P="ping -I uesimtun0 -c1 -W1 192.168.60.20"; else P="ping -c1 -W1 $IP"; fi
now() { date +%s.%N; }
echo "attente de la panne..."
while true; do T=$(now); if ! $P >/dev/null 2>&1; then T0=$T; break; fi; sleep 0.2; done
echo "panne détectée à $(date +%T)"
RESTARTED=non
while ! $P >/dev/null 2>&1; do
  if [ "$MODE" = ue ] && [ $RESTARTED = non ] && awk -v a=$T0 -v b=$(now) -v w=$WAIT 'BEGIN{exit !(b-a>w)}'; then
    echo "pas de reprise automatique en $WAIT s -> docker restart ue1"
    docker restart ue1 >/dev/null; RESTARTED=oui; sleep 6
  fi
  sleep 0.2
done
awk -v a=$T0 -v b=$(now) -v r=$RESTARTED 'BEGIN{printf "service rétabli après %.1f s (relance UE : %s)\n", b-a, r}'
