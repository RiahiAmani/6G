#!/bin/bash
# load.sh <port> <durée_s> <parallèle> <n> <sortie.csv> : charge continue depuis l'UE
export LC_ALL=C
D=$(cd "$(dirname "$0")" && pwd)
PORT=$1; DUR=${2:-240}; PAR=${3:-20}; N=${4:-300000}; export OUT=${5:-/tmp/load.csv}
export URL="http://192.168.60.20:$PORT/process?n=$N"
echo "t_fin,code,total_s" > "$OUT"
timeout $DUR bash -c "yes | xargs -P $PAR -I{} $D/one_req.sh"
pkill -f 'curl.*uesimtun0' 2>/dev/null
exit 0
