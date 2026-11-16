#!/bin/bash
# run_hpa.sh <essai> : 30 s sans charge, 150 s de charge, puis retour au calme
export LC_ALL=C
E=${1:?numéro d'essai}
S=$HOME/6G/a-infra/a8-k8s/scripts; R=$HOME/6G/a-infra/a8-k8s/results; mkdir -p $R
URL="http://192.168.60.20:30081/process?n=100000"
kubectl scale deploy mec-demo --replicas=1 >/dev/null
until [ "$(kubectl get pods -l app=mec-demo --no-headers | wc -l)" = 1 ]; do sleep 1; done
sleep 20
( echo "t,replicas,ready,cpu_percent,desired" > $R/hpa_$E.csv
  while true; do
    D=$(kubectl get deploy mec-demo -o jsonpath='{.status.replicas},{.status.readyReplicas}')
    H=$(kubectl get hpa mec-demo -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization},{.status.desiredReplicas}')
    echo "$(date +%s),$D,$H" >> $R/hpa_$E.csv; sleep 5
  done ) &
OBS=$!
$S/probe.sh "$URL" 450 $R/probe_hpa_$E.csv 40 &
PROBE=$!
sleep 30
T0=$(date +%s)
ab -s 60 -t 150 -c 20 "$URL" > $R/ab_$E.txt 2>&1
T1=$(date +%s)
printf "load_start=%s\nload_end=%s\n" $T0 $T1 > $R/meta_$E.txt
echo "charge terminée, attente du retour au calme..."
for i in $(seq 1 90); do
  [ "$(kubectl get deploy mec-demo -o jsonpath='{.status.replicas}')" = 1 ] && break; sleep 5
done
sleep 10
kill $OBS $PROBE 2>/dev/null; pkill -f probe.sh 2>/dev/null
grep -E "Complete requests|Failed requests|Requests per second|Time per request" $R/ab_$E.txt
python3 $S/hpa_report.py $E
