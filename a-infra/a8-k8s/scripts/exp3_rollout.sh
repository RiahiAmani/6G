#!/bin/bash
# exp3_rollout.sh rolling|recreate [tag] : mise à jour du déploiement (3 répétitions, 4 réplicas)
export LC_ALL=C
M=${1:-rolling}; TAG=${2:-}
S=$HOME/6G/a-infra/a8-k8s/scripts; R=$HOME/6G/a-infra/a8-k8s/results; mkdir -p $R
now(){ date +%s.%N; }
kubectl scale deploy mec-demo --replicas=4 >/dev/null
if [ "$M" = recreate ]; then
  kubectl patch deploy mec-demo -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}' >/dev/null
else
  kubectl patch deploy mec-demo -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":"25%","maxUnavailable":"25%"}}}}' >/dev/null
fi
kubectl rollout status deploy/mec-demo --timeout=120s >/dev/null
F=$R/rollout_${M}${TAG}.csv; echo "run,duree_s" > $F
for i in 1 2 3; do
  $S/probe.sh http://localhost:30081/ 45 $R/probe_rollout_${M}${TAG}_$i.csv 3 &
  sleep 5
  t0=$(now)
  kubectl set env deploy/mec-demo VERSION=${M}${TAG}-$i >/dev/null
  kubectl rollout status deploy/mec-demo --timeout=180s >/dev/null
  t1=$(now)
  awk -v i=$i -v a=$t0 -v b=$t1 'BEGIN{printf "%d,%.1f\n", i, b-a}' | tee -a $F
  wait
  python3 $S/probe_stats.py $R/probe_rollout_${M}${TAG}_$i.csv
  sleep 3
done
