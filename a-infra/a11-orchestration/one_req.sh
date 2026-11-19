#!/bin/bash
# une requête de charge (appelée par load.sh) ; ajoute « heure de fin, code HTTP, durée » à $OUT
r=$(curl -s -o /dev/null -m 60 --interface uesimtun0 -w "%{http_code},%{time_total}" "$URL")
echo "$(date +%s.%N),$r" >> "$OUT"
