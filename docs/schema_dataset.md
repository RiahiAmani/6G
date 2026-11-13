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
## Colonnes ajoutées au traitement
- `*_norm` : version z-score des variables numériques
- `label_id` : 0 = normal, 1 = congestion, 2 = anomaly

## Provenance
Dataset v1 : synthétique (graine 42), 30 UE, 600 s, 3 cellules.
Sera enrichi avec des traces SUMO (V2X) et ns-3 sans changer les colonnes.
## Dataset mobilité SUMO (dataset_6g_mobility.csv)
- Issus de SUMO : timestamp, ue_id, x, y, speed ; calculés à partir des positions : cell_id, handover, load_pct.
- Modélisés (hypothèses, pas des mesures) : throughput, latency, jitter, loss (formules dépendant de la charge).
- label : congestion si load_pct >= 85 %. Pas de label anomaly dans ce fichier.
- Capacité fixée à 20 UE/cellule (4 cellules) pour obtenir ~6 % de congestion : choix de modélisation.
- Limite : chaque véhicule traverse la grille en peu de temps (138 handovers pour 150 UE).
## Dataset NTN (dataset_6g_ntn.csv)
- Issus de Skyfield/SGP4 : cell_id (satellite servant = le plus proche, élévation >= 25°), handover (changement de satellite), délai de propagation.
- Modélisés (hypothèses) : débit, gigue, charge, traitement de 15 ms ajouté à la latence.
- Les 10 UE sont fixes et identiques (même position), donc leurs lignes ne sont pas indépendantes : seul le bruit modélisé les distingue.
- label = anomaly uniquement quand aucun satellite n'est visible (coupure). Ce n'est pas une anomalie injectée.
- Limite : sélection du satellite le plus proche à chaque pas de 30 s, sans coût de bascule ni signalisation. À 30 s de pas, des handovers entre deux pas peuvent être manqués.
