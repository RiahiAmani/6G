#!/bin/bash
# deploy_services.sh : supprime les services de l'atelier 10 puis déploie la configuration statique
cd "$(dirname "$0")"
kubectl delete deploy mec-edge mec-fog mec-cloud mec-demo --ignore-not-found
kubectl delete svc mec-edge mec-fog mec-cloud mec-demo --ignore-not-found
kubectl delete hpa --all --ignore-not-found
for s in urllc:edge:30101:2 embb:fog:30102:1 mmtc:cloud:30103:1; do
  IFS=: read SVC TIER PORT REPLICAS <<< "$s"; export SVC TIER PORT REPLICAS
  envsubst < service.yaml.tpl | kubectl apply -f -
done
for s in urllc embb mmtc; do kubectl rollout status deploy/$s --timeout=150s; done
kubectl get pods -l 'app in (urllc,embb,mmtc)' -o wide
