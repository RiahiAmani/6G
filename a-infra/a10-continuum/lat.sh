#!/bin/bash
# lat.sh <étiquette> [runs] [séries] : latence réseau pure vers chaque tier (requête sur « / », sans calcul)
export LC_ALL=C
source "$HOME/6G/a-infra/a7-vm/scripts/ue_guard.sh"
R=$HOME/6G/a-infra/a10-continuum/results; mkdir -p $R
L=${1:?usage: lat.sh <sans_netem|avec_netem> [runs] [séries]}; RUNS=${2:-30}; SERIES=${3:-3}
OUT=$R/lat_$L.csv; echo "serie,tier,connect_ms,total_ms" > $OUT
for s in $(seq 1 $SERIES); do
  ensure_ue || exit 1
  for t in edge:30081 fog:30082 cloud:30083; do
    tier=${t%%:*}; port=${t##*:}
    for i in $(seq 1 $RUNS); do
      curl -s -o /dev/null -m 10 --interface uesimtun0 -w '%{time_connect},%{time_total}' "http://192.168.60.20:$port/" \
        | awk -F, -v s=$s -v t=$tier '{printf "%d,%s,%.2f,%.2f\n", s, t, $1*1000, $2*1000}' >> $OUT
    done
  done
done
echo "résultats : $OUT"
