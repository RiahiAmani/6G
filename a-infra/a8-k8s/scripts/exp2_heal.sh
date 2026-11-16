#!/bin/bash
# exp2_heal.sh one|all : suppression d'un pod / de tous les pods (3 répétitions)
export LC_ALL=C
M=${1:-one}
S=$HOME/6G/a-infra/a8-k8s/scripts; R=$HOME/6G/a-infra/a8-k8s/results; mkdir -p $R
now(){ date +%s.%N; }
ready(){ kubectl get deploy mec-demo -o jsonpath='{.status.readyReplicas}'; }
kubectl scale deploy mec-demo --replicas=2 >/dev/null
until [ "$(ready)" = 2 ]; do sleep 0.5; done
echo "run,remplacement_s" > $R/heal_$M.csv
for i in 1 2 3; do
  $S/probe.sh http://localhost:30081/ 40 $R/probe_heal_${M}_$i.csv 3 &
  sleep 5
  if [ $M = one ]; then DEL=$(kubectl get pods -l app=mec-demo -o name | head -1)
  else DEL=$(kubectl get pods -l app=mec-demo -o name); fi
  t0=$(now)
  kubectl delete $DEL --wait=false >/dev/null
  while true; do
    left=$(kubectl get pods -l app=mec-demo -o name | grep -c -F -x "$DEL")
    [ "$left" = 0 ] && [ "$(ready)" = 2 ] && break
    sleep 0.2
  done
  t1=$(now)
  awk -v i=$i -v a=$t0 -v b=$t1 'BEGIN{printf "%d,%.1f\n", i, b-a}' | tee -a $R/heal_$M.csv
  wait
  python3 $S/probe_stats.py $R/probe_heal_${M}_$i.csv
  sleep 3
done
