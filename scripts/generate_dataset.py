import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_UE = 30
DURATION = 600          # secondes
CELLS = {"cell_1": (200, 200), "cell_2": (800, 200), "cell_3": (500, 700)}
PROFILES = {            # débit, latence, gigue moyens par type
    "embb":  dict(thr=50.0, lat=20.0, jit=3.0),
    "urllc": dict(thr=5.0,  lat=5.0,  jit=0.5),
    "mmtc":  dict(thr=0.1,  lat=50.0, jit=8.0),
}

rows = []
types = rng.choice(list(PROFILES), size=N_UE, p=[0.4, 0.3, 0.3])

for i in range(N_UE):
    ue_id = f"ue_{i+1:03d}"
    t_ue = types[i]
    p = PROFILES[t_ue]
    pos = rng.uniform(0, 1000, 2)
    vel = rng.normal(0, 1, 2) * (10 if t_ue == "urllc" else 1.5)
    prev_cell = None
    for t in range(DURATION):
        pos = pos + vel + rng.normal(0, 0.5, 2)
        for k in (0, 1):                      # rebond sur les bords
            if pos[k] < 0 or pos[k] > 1000:
                vel[k] *= -1
                pos[k] = np.clip(pos[k], 0, 1000)
        dists = {c: np.hypot(pos[0]-cx, pos[1]-cy) for c, (cx, cy) in CELLS.items()}
        cell = min(dists, key=dists.get)
        ho = int(prev_cell is not None and cell != prev_cell)
        prev_cell = cell
        rows.append(dict(
            timestamp=float(t), ue_id=ue_id, ue_type=t_ue, slice=t_ue,
            cell_id=cell, x=pos[0], y=pos[1], speed=float(np.hypot(*vel)),
            throughput_mbps=max(0, rng.normal(p["thr"], p["thr"]*0.1)),
            latency_ms=max(0.1, rng.normal(p["lat"], p["lat"]*0.1)),
            jitter_ms=max(0.01, rng.normal(p["jit"], p["jit"]*0.2)),
            loss_pct=max(0, rng.normal(0.2, 0.1)),
            load_pct=float(np.clip(rng.normal(50, 10), 0, 100)),
            handover=ho, label="normal"))

df = pd.DataFrame(rows)

# Injection d'anomalies et de congestion (étiquettes connues)
n = len(df)
idx_cong = rng.choice(n, size=int(0.03*n), replace=False)
df.loc[idx_cong, ["load_pct"]] = rng.uniform(85, 100, len(idx_cong))
df.loc[idx_cong, "latency_ms"] *= rng.uniform(2, 4, len(idx_cong))
df.loc[idx_cong, "label"] = "congestion"

idx_anom = rng.choice(np.setdiff1d(np.arange(n), idx_cong), size=int(0.02*n), replace=False)
df.loc[idx_anom, "throughput_mbps"] *= rng.uniform(5, 10, len(idx_anom))
df.loc[idx_anom, "loss_pct"] = rng.uniform(5, 20, len(idx_anom))
df.loc[idx_anom, "label"] = "anomaly"

df.round(3).to_csv("data/raw/dataset_6g_raw.csv", index=False)
print(df.shape)
print(df["label"].value_counts())
