#!/bin/bash
# run_a10.sh [runs] [séries] : balayage UE / Edge / Fog / Cloud pour plusieurs tailles de tâche
# variables : TAG (netem par défaut), SIZES
export LC_ALL=C
source "$HOME/6G/a-infra/a7-vm/scripts/ue_guard.sh"
D=$HOME/6G/a-infra/a10-continuum; R=$D/results; mkdir -p $R
RUNS=${1:-10}; SERIES=${2:-3}
SIZES=${SIZES:-"50000 200000 400000 800000 1600000 3000000"}
OUT=$R/results_${TAG:-netem}.csv
echo "serie,tier,n,connect,total,proc_ms" > $OUT
for n in $SIZES; do
  for s in $(seq 1 $SERIES); do
    ensure_ue || exit 1
    python3 $D/measure_local.py $RUNS $n $s >> $OUT
    for t in edge:30081 fog:30082 cloud:30083; do $D/measure.sh ${t%%:*} ${t##*:} $RUNS $n $OUT $s; done
  done
  echo "n=$n terminé ($(date +%T))"
done
echo "résultats : $OUT"
