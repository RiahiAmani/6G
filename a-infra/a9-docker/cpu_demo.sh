#!/bin/bash
# cpu_demo.sh : même charge sur un conteneur limité (0,5 CPU) et sur un conteneur sans limite
cd "$(dirname "$0")"
docker rm -f mec-free >/dev/null 2>&1
docker run -d --name mec-free -p 18081:8080 -e TIER=free -e NODE_NAME=compose mec-app:1.0 >/dev/null
sleep 4
curl -s -o /dev/null http://127.0.0.1:8080/ && curl -s -o /dev/null http://127.0.0.1:18081/ \
  || { echo "un des deux services ne répond pas"; exit 1; }
ab -t 15 -c 4 "http://127.0.0.1:8080/process?n=200000"  > /tmp/ab_limit.txt 2>&1 &
ab -t 15 -c 4 "http://127.0.0.1:18081/process?n=200000" > /tmp/ab_free.txt 2>&1 &
sleep 7
docker stats --no-stream mec-app mec-free
wait
for f in limit free; do
  echo "== $f"
  grep -E "Complete requests|Failed requests|Requests per second|Time per request" /tmp/ab_$f.txt
  grep -A1 "Failed requests" /tmp/ab_$f.txt | tail -1
done
