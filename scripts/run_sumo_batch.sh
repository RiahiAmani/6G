#!/bin/bash
# Regenere les 9 simulations SUMO (3 densites x 3 graines)
set -e
cd "$(dirname "$0")/.."
mkdir -p sumo/runs
[ -f sumo/grid.net.xml ] || netgenerate --grid --grid.number=5 --grid.length=200 -o sumo/grid.net.xml
for p in 4 2 1; do
  for seed in 1 2 3; do
    python $SUMO_HOME/tools/randomTrips.py -n sumo/grid.net.xml -e 300 -p $p \
      --seed $seed -r sumo/runs/p${p}_s${seed}.rou.xml
    sumo -n sumo/grid.net.xml -r sumo/runs/p${p}_s${seed}.rou.xml --end 300 \
      --seed $seed --no-step-log --fcd-output sumo/runs/p${p}_s${seed}.fcd.xml
  done
done
