#!/bin/bash
# iperf_ue.sh <étiquette> [répétitions] [secondes] : débit UE -> vm-k8s (montant puis descendant)
export LC_ALL=C
L=${1:-test}; N=${2:-3}; T=${3:-20}
R=$HOME/6G/a-infra/a7-vm/results; mkdir -p $R
echo "label,run,sens,mbps" > $R/iperf_$L.csv
for i in $(seq 1 $N); do
  for sens in up down; do
    OPT=""; [ $sens = down ] && OPT="-R"
    M=$(iperf3 -c 192.168.60.20 --bind-dev uesimtun0 -t $T $OPT -J | jq -r '.end.sum_received.bits_per_second/1e6*100|round/100')
    echo "$L,$i,$sens,$M" | tee -a $R/iperf_$L.csv
  done
done
