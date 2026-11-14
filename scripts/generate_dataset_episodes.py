"""Dataset v1-episodes : memes colonnes que la v1, mais congestions et attaques en EPISODES
sur une cellule (plusieurs secondes, tous les UE de la cellule), avec plusieurs intensites.
Fichiers : dataset_6g_episodes.csv (schema v1.0) + episodes_meta.csv + episodes_rows.csv"""
import sys
import numpy as np
import pandas as pd
from generate_dataset import base_dataset

INTENS = {"faible": (1.2, 0.2), "moyenne": (2.0, 2.0), "forte": (8.0, 12.0)}  # (facteur debit, perte ajoutee %)

def generate_episodes(seed=42, n_cong=4, n_att=6, duration=600):
    rng = np.random.default_rng(seed)
    df = base_dataset(rng)
    cells = sorted(df.cell_id.unique())
    kinds = ["congestion"] * n_cong + ["attaque"] * n_att
    rng.shuffle(kinds)
    durs = [int(rng.integers(15, 41)) if k == "congestion" else int(rng.integers(5, 31)) for k in kinds]
    gaps = rng.dirichlet(np.ones(len(kinds) + 1)) * (duration - sum(durs) - 10)
    inten_cycle = list(INTENS) * ((n_att + 2) // 3)
    rng.shuffle(inten_cycle)
    meta, rowlab, t = [], [], 5.0
    ia = 0
    df["episode_id"] = -1
    for e, (k, d, g) in enumerate(zip(kinds, durs, gaps)):
        t0 = int(t + g); t1 = t0 + d - 1; t = t1 + 1
        cell = cells[int(rng.integers(len(cells)))]
        inten = "-" if k == "congestion" else inten_cycle[ia]
        ia += k == "attaque"
        m = (df.timestamp >= t0) & (df.timestamp <= t1) & (df.cell_id == cell)
        idx = df.index[m]
        r = np.minimum(1.0, (df.loc[idx, "timestamp"].values - t0 + 1) / (0.3 * d)) if k == "congestion" else np.ones(len(idx))
        if k == "congestion":
            df.loc[idx, "load_pct"] = np.maximum(df.loc[idx, "load_pct"].values, 50 + r * (rng.uniform(88, 100, len(idx)) - 50))
            df.loc[idx, "latency_ms"] = df.loc[idx, "latency_ms"].values * (1 + r * rng.uniform(1, 3, len(idx)))
            df.loc[idx, "label"] = "congestion"
        else:
            mult, loss = INTENS[inten]
            df.loc[idx, "throughput_mbps"] = df.loc[idx, "throughput_mbps"].values * mult * rng.uniform(0.95, 1.05, len(idx))
            df.loc[idx, "loss_pct"] = df.loc[idx, "loss_pct"].values + loss * rng.uniform(0.9, 1.1, len(idx))
            df.loc[idx, "label"] = "anomaly"
        df.loc[idx, "episode_id"] = e
        meta.append(dict(episode_id=e, type=k, cell=cell, t_start=t0, t_end=t1, duree_s=d, intensite=inten, n_lignes=len(idx)))
    meta = pd.DataFrame(meta)
    rows = df[df.episode_id >= 0][["timestamp", "ue_id", "episode_id"]].merge(meta[["episode_id", "type", "intensite"]], on="episode_id")
    cols = [c for c in df.columns if c != "episode_id"]
    return df[cols].round(3), meta, rows

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    df, meta, rows = generate_episodes(seed)
    df.to_csv("data/processed/dataset_6g_episodes.csv", index=False)
    meta.to_csv("data/processed/episodes_meta.csv", index=False)
    rows.to_csv("data/processed/episodes_rows.csv", index=False)
    print(df.shape, df.label.value_counts().to_dict())
    print("Prevalence anormale : %.1f %%" % (100 * (df.label != "normal").mean()))
    print(meta.to_string(index=False))
