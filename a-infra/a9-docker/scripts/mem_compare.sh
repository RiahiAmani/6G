#!/bin/bash
# mem_compare.sh : RAM de la VM avec et sans le conteneur UPF (3 répétitions)
echo "run,ram_utilisee_avec_upf_mo,ram_utilisee_sans_upf_mo,ecart_mo,rss_processus_upf_mo,docker_stats_mo"
for i in 1 2 3; do
  docker start upf >/dev/null 2>&1; sleep 20
  A=$(free -m | awk '/Mem/{print $3}')
  RSS=$(ps -o rss= -C open5gs-upfd | awk '{s+=$1} END{printf "%.1f", s/1024}')
  DS=$(docker stats --no-stream --format '{{.MemUsage}}' upf | awk '{print $1}')
  docker stop upf >/dev/null; sleep 10
  B=$(free -m | awk '/Mem/{print $3}')
  echo "$i,$A,$B,$((A-B)),$RSS,$DS"
done | tee ~/6G/a-infra/a9-docker/results/mem_compare.csv
docker start upf >/dev/null
