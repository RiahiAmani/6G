import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

FCD = "sumo/runs/p2_s1.fcd.xml"                 # densité moyenne, graine 1
CELLS = {"cell_1": (200, 200), "cell_2": (600, 200),
         "cell_3": (200, 600), "cell_4": (600, 600)}
CAPACITY = 20   # UE par cellule à 100 % de charge
rng = np.random.default_rng(42)

rows = []
for _, el in ET.iterparse(FCD, events=("end",)):
    if el.tag == "timestep":
        t = float(el.get("time"))
        for v in el.findall("vehicle"):
            rows.append((t, "veh_" + v.get("id"), float(v.get("x")),
                         float(v.get("y")), float(v.get("speed"))))
        el.clear()
df = pd.DataFrame(rows, columns=["timestamp", "ue_id", "x", "y", "speed"])
df = df.sort_values(["ue_id", "timestamp"]).reset_index(drop=True)

# Cellule la plus proche + handover
names = list(CELLS)
dist = np.stack([np.hypot(df.x - cx, df.y - cy) for cx, cy in CELLS.values()], axis=1)
df["cell_id"] = [names[i] for i in dist.argmin(axis=1)]
prev = df.groupby("ue_id")["cell_id"].shift()
df["handover"] = ((prev.notna()) & (prev != df["cell_id"])).astype(int)

# Charge = UE présents dans la cellule au même instant
count = df.groupby(["timestamp", "cell_id"])["ue_id"].transform("count")
df["load_pct"] = (100 * count / CAPACITY).clip(0, 100)

# QoS modélisée (profil URLLC, dégradée par la charge) : hypothèse, pas une mesure
n = len(df)
df["ue_type"] = df["slice"] = "urllc"
df["throughput_mbps"] = np.clip(rng.normal(5.0, 0.5, n) * (1 - 0.4 * df.load_pct / 100), 0, None)
df["latency_ms"] = np.clip(rng.normal(5.0, 0.5, n) * (1 + df.load_pct / 100), 0.1, None)
df["jitter_ms"] = np.clip(rng.normal(0.5, 0.1, n) * (1 + df.load_pct / 100), 0.01, None)
df["loss_pct"] = np.clip(rng.normal(0.2, 0.1, n) + 0.5 * (df.load_pct / 100) ** 2, 0, None)
df["label"] = np.where(df.load_pct >= 85, "congestion", "normal")

cols = ["timestamp", "ue_id", "ue_type", "slice", "cell_id", "x", "y", "speed",
        "throughput_mbps", "latency_ms", "jitter_ms", "loss_pct", "load_pct",
        "handover", "label"]
df = df[cols].round(3)
df.to_csv("data/processed/dataset_6g_mobility.csv", index=False)
print(df.shape)
print(df["label"].value_counts())
print("handovers:", df.handover.sum(), "| UE:", df.ue_id.nunique())
print(df.groupby("cell_id")["load_pct"].mean().round(1))
