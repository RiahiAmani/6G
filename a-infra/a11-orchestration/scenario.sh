#!/bin/bash
# scenario.sh <sta|dyn> <essai> : calme, charge URLLC, retour au calme (+ sondes sur les 3 services)
export LC_ALL=C
source "$HOME/6G/a-infra/a7-vm/scripts/ue_guard.sh"
D=$HOME/6G/a-infra/a11-orchestration; R=$D/results; mkdir -p $R
P=$HOME/6G/a-infra/a8-k8s/scripts/probe.sh
MODE=${1:?usage: scenario.sh sta|dyn <essai>}; RUN=${2:?}; TAG=${MODE}_${RUN}
BASE=${BASE:-30}; LOAD=${LOAD:-240}; REC=${REC:-150}; PAR=${PAR:-20}; N=${N:-300000}
ensure_ue || exit 1
TOT=$((BASE+LOAD+REC))
for s in urllc:30101 embb:30102 mmtc:30103; do
  IFACE=uesimtun0 $P "http://192.168.60.20:${s##*:}/" $TOT $R/probe_${TAG}_${s%%:*}.csv 10 &
done
echo "$(date +%T) $TAG : $BASE s de calme"
sleep $BASE
T0=$(date +%s.%N)
echo "$(date +%T) début de la charge URLLC ($LOAD s)"
$D/load.sh 30101 $LOAD $PAR $N $R/load_$TAG.csv
T1=$(date +%s.%N)
printf "load_start=%s\nload_end=%s\nmode=%s\n" $T0 $T1 $MODE > $R/meta_$TAG.txt
echo "$(date +%T) fin de la charge ; retour au calme ($REC s)"
wait
echo "terminé : $TAG"
