import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/dataset_6g_raw.csv")
print("Taille brute :", df.shape)

# 1. Qualité : valeurs manquantes et doublons
print("\nValeurs manquantes :\n", df.isna().sum()[df.isna().sum() > 0])
before = len(df)
df = df.drop_duplicates(subset=["timestamp", "ue_id"])
print("Doublons supprimés :", before - len(df))

# 2. Types et cohérence
df = df.sort_values(["ue_id", "timestamp"]).reset_index(drop=True)
assert df["ue_type"].isin(["embb", "urllc", "mmtc"]).all()
assert df["label"].isin(["normal", "congestion", "anomaly"]).all()
assert df["load_pct"].between(0, 100).all()

# 3. Normalisation z-score des variables numériques (colonnes *_norm)
#    Les colonnes brutes sont conservées : B et D peuvent utiliser l'une ou l'autre.
num_cols = ["x", "y", "speed", "throughput_mbps", "latency_ms",
            "jitter_ms", "loss_pct", "load_pct"]
for c in num_cols:
    df[c + "_norm"] = (df[c] - df[c].mean()) / df[c].std()

# 4. Encodage du label pour les modèles (0 normal, 1 congestion, 2 anomaly)
df["label_id"] = df["label"].map({"normal": 0, "congestion": 1, "anomaly": 2})

df.to_csv("data/processed/dataset_6g.csv", index=False)
print("\nTaille finale :", df.shape)
print(df.groupby("ue_type")[["throughput_mbps", "latency_ms", "jitter_ms"]].mean().round(2))
