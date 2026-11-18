#!/bin/bash
# reg_time.sh : durée « lancement du conteneur UE -> uesimtun0 disponible » (secondes, point décimal)
export LC_ALL=C
RUNS=${1:-10}
echo "run,registration_s" > reg_times.csv
for i in $(seq 1 $RUNS); do
  docker rm -f ue1 >/dev/null 2>&1; sleep 2
  t0=$(date +%s.%N)
  docker run -d --name ue1 --network host --privileged \
    -v $PWD/ue.yaml:/ueransim/config/ue.yaml:ro ${IMG:-ueransim:local} ./build/nr-ue -c config/ue.yaml >/dev/null
  until ip link show uesimtun0 >/dev/null 2>&1; do sleep 0.05; done
  t1=$(date +%s.%N)
  awk -v i=$i -v a=$t0 -v b=$t1 'BEGIN{printf "%d,%.3f\n", i, b-a}' | tee -a reg_times.csv
done
for i in 1 2 3; do ping -I uesimtun0 -c 20 -q 192.168.60.20 | tail -1; done
