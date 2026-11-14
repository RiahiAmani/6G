"""Robustesse du generateur v1 : 3 graines, moyenne et ecart-type de quelques statistiques."""
import numpy as np
import pandas as pd
from generate_dataset import generate

SEEDS = (42, 43, 44)
rows = []
for s in SEEDS:
    df = generate(s)
    ue = df.drop_duplicates("ue_id").ue_type.value_counts()
    r = dict(seed=s,
             n_embb=int(ue.get("embb", 0)), n_urllc=int(ue.get("urllc", 0)), n_mmtc=int(ue.get("mmtc", 0)),
             handovers=int(df.handover.sum()),
             cong_pct=100 * (df.label == "congestion").mean(),
             anom_pct=100 * (df.label == "anomaly").mean())
    for t in ("embb", "urllc", "mmtc"):
        sub = df[df.ue_type == t]
        r[f"{t}_thr"] = sub.throughput_mbps.mean()
        r[f"{t}_lat"] = sub.latency_ms.mean()
        r[f"{t}_jit"] = sub.jitter_ms.mean()
    rows.append(r)

res = pd.DataFrame(rows)
res.to_csv("data/processed/dataset_seeds_stats.csv", index=False)
print(res.round(2).to_string(index=False))
print()
print(res.drop(columns="seed").agg(["mean", "std"]).round(2).T.to_string())
