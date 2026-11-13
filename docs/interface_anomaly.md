# Interface de détection d'anomalies (atelier 25 -> atelier 27)

## Utilisation
from scripts.anomaly_api import score_rows
alerts = score_rows(df)   # df au schéma v1.0

Entrée : timestamp, ue_id, ue_type (embb/urllc/mmtc), throughput_mbps,
latency_ms, jitter_ms, loss_pct, load_pct.
Sortie : timestamp, ue_id, score (0 à 1), is_anomaly (bool), method.

## Limites
- score = score brut Isolation Forest ramené à [0,1] par min-max sur le
  dataset d'entraînement : ce n'est PAS une probabilité.
- Modèle entraîné sur tout dataset_6g.csv : scores en échantillon, ne pas
  s'en servir pour rapporter des performances (voir atelier 25).
- is_anomaly signale environ 5 % des lignes (contamination=0.05) ; pour un
  trafic d'attaque plus fréquent, utiliser score avec un seuil propre.
- Chaque ligne est jugée isolément (pas de contexte temporel).
