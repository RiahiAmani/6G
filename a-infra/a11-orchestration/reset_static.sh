#!/bin/bash
# reset_static.sh : remet chaque service sur son tier statique, avec le bon nombre de réplicas
declare -A T=( [urllc]=edge [embb]=fog [mmtc]=cloud )
for s in urllc embb mmtc; do
  t=${T[$s]}
  kubectl patch deploy $s -p "{\"spec\":{\"template\":{\"metadata\":{\"labels\":{\"tier\":\"$t\"}},\"spec\":{\"nodeSelector\":{\"tier\":\"$t\"},\"containers\":[{\"name\":\"app\",\"env\":[{\"name\":\"TIER\",\"value\":\"$t\"}]}]}}}}" >/dev/null
done
kubectl scale deploy urllc --replicas=2 >/dev/null
kubectl scale deploy embb mmtc --replicas=1 >/dev/null
for s in urllc embb mmtc; do kubectl rollout status deploy/$s --timeout=150s >/dev/null; done
sleep 40      # laisse retomber le CPU mesuré par metrics-server
kubectl get pods -l 'app in (urllc,embb,mmtc)' -o wide
