#!/bin/bash
# vm_boot_report.sh : à lancer sur vm-upf environ 90 s après un redémarrage de la VM
export LC_ALL=C
R=$HOME/6G/a-infra/a9-docker/results; mkdir -p $R; F=$R/startup_vm.csv
[ -f $F ] || echo "date,boot_to_upf_start_s,boot_to_pfcp_associated_s" > $F
BOOT=$(date -d "$(uptime -s)" +%s)
ST=$(docker inspect upf --format '{{.State.StartedAt}}')
STE=$(date -d "$ST" +%s.%N); STI=$(date -d "$ST" +%s)
A=$(docker logs -t --since $STI upf 2>&1 | grep -m1 'PFCP associated' | cut -d' ' -f1)
[ -z "$A" ] && { echo "pas d'association PFCP vue (vm-cp et son SMF tournent-ils ?)"; exit 1; }
AE=$(date -d "$A" +%s.%N)
awk -v d="$(date +%F_%T)" -v b=$BOOT -v s=$STE -v a=$AE 'BEGIN{printf "%s,%.1f,%.1f\n", d, s-b, a-b}' | tee -a $F
echo "--- systemd-analyze :"; systemd-analyze 2>/dev/null | head -1
echo "--- services les plus longs :"; systemd-analyze blame 2>/dev/null | head -5
