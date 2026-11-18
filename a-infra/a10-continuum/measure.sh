#!/bin/bash
# usage : ./measure.sh <tier> <port> <runs> <n> <sortie.csv> <série>
# colonnes écrites : serie,tier,n,connect,total,proc_ms   (temps en secondes, proc_ms en ms)
export LC_ALL=C
TIER=$1; PORT=$2; RUNS=${3:-10}; N=${4:-200000}; OUT=${5:-results.csv}; SERIE=${6:-1}; IP=192.168.60.20
for i in $(seq 1 $RUNS); do
  out=$(curl -s -m 60 --interface uesimtun0 -w '\n%{time_connect},%{time_total}' "http://$IP:$PORT/process?n=$N")
  proc=$(echo "$out" | head -n1 | jq -r .proc_ms 2>/dev/null); t=$(echo "$out" | tail -n1)
  if [ -n "$proc" ] && [ "$proc" != null ]; then echo "$SERIE,$TIER,$N,$t,$proc" >> "$OUT"
  else echo "ECHEC : $TIER n=$N (requête $i)" >&2; fi
done
