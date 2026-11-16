#!/bin/bash
# exp1_scale.sh : réplication manuelle 1 -> 5 -> 1, 3 répétitions
export LC_ALL=C
R=$HOME/6G/a-infra/a8-k8s/results; mkdir -p $R
now(){ date +%s.%N; }
count(){ kubectl get pods -l app=mec-demo --no-headers 2>/dev/null | wc -l; }
ready(){ kubectl get deploy mec-demo -o jsonpath='{.status.readyReplicas}'; }
echo "run,up_s,down_s" > $R/scale.csv
kubectl scale deploy mec-demo --replicas=1 >/dev/null
until [ "$(count)" = 1 ] && [ "$(ready)" = 1 ]; do sleep 0.5; done
for i in 1 2 3; do
  t0=$(now); kubectl scale deploy mec-demo --replicas=5 >/dev/null
  until [ "$(ready)" = 5 ]; do sleep 0.2; done; t1=$(now)
  echo "-- répartition des 5 pods (essai $i) :"
  kubectl get pods -l app=mec-demo -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort | uniq -c
  sleep 3
  t2=$(now); kubectl scale deploy mec-demo --replicas=1 >/dev/null
  until [ "$(count)" = 1 ]; do sleep 0.2; done; t3=$(now)
  awk -v i=$i -v a=$t0 -v b=$t1 -v c=$t2 -v d=$t3 'BEGIN{printf "%d,%.1f,%.1f\n", i, b-a, d-c}' | tee -a $R/scale.csv
  sleep 5
done
python3 -c "
import pandas as pd
d = pd.read_csv('$R/scale.csv')
print(d[['up_s','down_s']].agg(['mean','std']).round(2))"
