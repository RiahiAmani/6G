#!/bin/bash
# deploy_tiers.sh : supprime mec-demo (atelier 8) puis déploie un service par tier
cd "$(dirname "$0")"
kubectl delete -f ../a8-k8s/deploy.yaml --ignore-not-found
for t in edge:30081:500m fog:30082:800m cloud:30083:1500m; do
  IFS=: read TIER PORT CPU_LIMIT <<< "$t"; export TIER PORT CPU_LIMIT
  envsubst < tier.yaml.tpl | kubectl apply -f -
done
for t in edge fog cloud; do kubectl rollout status deploy/mec-$t --timeout=150s; done
kubectl get pods -l 'app in (mec-edge,mec-fog,mec-cloud)' -o wide
