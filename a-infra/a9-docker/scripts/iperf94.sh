#!/bin/bash
# iperf94.sh tcp|udp|parallel [répétitions] [durée_s] : débit vers le serveur iperf3 de vm-k8s
export LC_ALL=C
source "$HOME/6G/a-infra/a7-vm/scripts/ue_guard.sh"
SRV=192.168.60.20
R=$HOME/6G/a-infra/a9-docker/results; mkdir -p "$R"
MODE=${1:?usage: iperf94.sh tcp|udp|parallel [répétitions] [durée]}; N=${2:-3}; T=${3:-15}

ip_run() {   # ip_run <ue|direct> [options iperf3]  -> JSON sur stdout
  local via=$1; shift
  if [ "$via" = ue ]; then iperf3 -c $SRV --bind-dev uesimtun0 -t $T -J "$@"
  else iperf3 -c $SRV -t $T -J "$@"; fi
}
check() { local e; e=$(echo "$1" | jq -r '.error // empty' 2>/dev/null); [ -n "$e" ] && echo "ERREUR : $e" >&2 && return 1; return 0; }

if [ "$MODE" = tcp ]; then
  F=$R/iperf_tcp.csv; echo "via,run,sens,mbps,retrans" > $F
  for via in ue direct; do
    for i in $(seq 1 $N); do
      for sens in up down; do
        [ $via = ue ] && { ensure_ue || exit 1; }
        OPT=""; [ $sens = down ] && OPT="-R"
        J=$(ip_run $via $OPT); check "$J" || continue
        M=$(echo "$J" | jq -r '.end.sum_received.bits_per_second/1e6*100|round/100')
        RT=$(echo "$J" | jq -r '.end.sum_sent.retransmits // 0')
        echo "$via,$i,$sens,$M,$RT" | tee -a $F
      done
    done
  done
elif [ "$MODE" = udp ]; then
  F=$R/iperf_udp.csv; echo "rate_mbps,run,mbps,jitter_ms,lost_pct" > $F
  for rate in 20 50 100 200; do
    for i in $(seq 1 $N); do
      ensure_ue || exit 1
      J=$(ip_run ue -u -b ${rate}M -l 1200); check "$J" || continue
      V=$(echo "$J" | jq -r '[(.end.sum.bits_per_second/1e6*100|round/100), (.end.sum.jitter_ms*1000|round/1000), (.end.sum.lost_percent*100|round/100)] | @csv')
      echo "$rate,$i,$V" | tee -a $F
    done
  done
elif [ "$MODE" = parallel ]; then
  F=$R/iperf_parallel.csv; echo "streams,run,mbps" > $F
  for p in 1 2 4 8; do
    for i in $(seq 1 $N); do
      ensure_ue || exit 1
      J=$(ip_run ue -P $p); check "$J" || continue
      echo "$p,$i,$(echo "$J" | jq -r '.end.sum_received.bits_per_second/1e6*100|round/100')" | tee -a $F
    done
  done
fi
