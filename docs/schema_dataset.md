# Schéma du dataset 6G (v1.0)

| Colonne | Type | Unité | Description |
|---|---|---|---|
| timestamp | float | s | Temps de simulation |
| ue_id | str | - | Identifiant de l'UE (ex. ue_001) |
| ue_type | str | - | embb / urllc / mmtc |
| slice | str | - | embb / urllc / mmtc |
| cell_id | str | - | Cellule de rattachement (ex. cell_1, sat_1) |
| x | float | m | Position X |
| y | float | m | Position Y |
| speed | float | m/s | Vitesse |
| throughput_mbps | float | Mbit/s | Débit |
| latency_ms | float | ms | Latence |
| jitter_ms | float | ms | Gigue |
| loss_pct | float | % | Pertes de paquets |
| load_pct | float | % | Charge de la cellule |
| handover | int | 0/1 | 1 si handover à cet instant |
| label | str | - | normal / congestion / anomaly |

Format : CSV, séparateur `,`, encodage UTF-8, point décimal, une ligne par (timestamp, ue_id).
Fréquence d'échantillonnage : 1 s.
