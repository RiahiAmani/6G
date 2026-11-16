#!/bin/bash
# bench.sh mono|distribue : enregistrement (10x), RTT (3x20 pings), débit (3x15 s)
export LC_ALL=C
L=${1:?usage: bench.sh mono|distribue}
R=$HOME/6G/a-infra/a7-vm/results; S=$HOME/6G/a-infra/a7-vm/scripts; mkdir -p $R
cd $HOME/6G/a-infra/a3-core-ran/ran
./reg_time.sh 10 > /dev/null 2>&1
cp reg_times.csv $R/reg_$L.csv
echo "serie,rtt_ms" > $R/rtt_$L.csv
for s in 1 2 3; do
  echo "$s,$(ping -I uesimtun0 -c 20 -q 192.168.60.20 | awk -F/ '/^rtt/{print $5}')" >> $R/rtt_$L.csv
done
$S/iperf_ue.sh $L 3 15
echo "== terminé : $R =="
