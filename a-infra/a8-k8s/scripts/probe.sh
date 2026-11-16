#!/bin/bash
# probe.sh <url> <durée_s> <sortie.csv> [timeout_s] : une requête toutes les 0,2 s
# (IFACE=uesimtun0 pour passer par l'UE, depuis vm-ran)
export LC_ALL=C
URL=${1:-http://localhost:30081/}; D=${2:-60}; OUT=${3:-probe.csv}; TO=${4:-5}
echo "t,code,total_ms" > $OUT
end=$(( $(date +%s) + D ))
while [ $(date +%s) -lt $end ]; do
  t=$(date +%s.%N)
  r=$(curl -s -o /dev/null -m $TO ${IFACE:+--interface $IFACE} -w '%{http_code},%{time_total}' "$URL")
  awk -v t=$t -v r="$r" 'BEGIN{split(r,a,","); printf "%.3f,%s,%.1f\n", t, a[1], a[2]*1000}' >> $OUT
  sleep 0.2
done
