#!/bin/bash
# upf_startup.sh [répétitions] : arrêt puis démarrage du conteneur UPF, avec 3 instants mesurés
export LC_ALL=C
N=${1:-5}
R=$HOME/6G/a-infra/a9-docker/results; mkdir -p $R; F=$R/startup_container.csv
echo "run,docker_start_s,init_done_s,pfcp_associated_s" > $F
now() { date +%s.%N; }
for i in $(seq 1 $N); do
  docker stop upf >/dev/null; sleep 3
  S=$(date +%s); t0=$(now)
  docker start upf >/dev/null; t1=$(now)
  t2=""; t3=""
  for k in $(seq 1 900); do
    L=$(docker logs --since $S upf 2>&1)
    [ -z "$t2" ] && echo "$L" | grep -q 'UPF initialize...done' && t2=$(now)
    if echo "$L" | grep -q 'PFCP associated'; then t3=$(now); break; fi
    sleep 0.1
  done
  awk -v i=$i -v a=$t0 -v b=$t1 -v c="${t2:-0}" -v d="${t3:-0}" \
    'BEGIN{printf "%d,%.3f,%.3f,%.3f\n", i, b-a, (c>0?c-a:-1), (d>0?d-a:-1)}' | tee -a $F
  sleep 5
done
