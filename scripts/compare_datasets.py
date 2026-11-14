"""Atelier 14 : comparaison des trois datasets au meme schema v1.0 (synthetique, SUMO, NTN)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DS = {  # nom : (fichier, pas d'echantillonnage en s)
    "v1 synthetique": ("data/processed/dataset_6g.csv", 1.0),
    "SUMO (mobilite)": ("data/processed/dataset_6g_mobility.csv", 1.0),
    "NTN (satellite)": ("data/processed/dataset_6g_ntn.csv", 30.0),
}
rows, data = [], {}
for name, (f, dt) in DS.items():
    d = pd.read_csv(f); data[name] = d
    ue_h = len(d) * dt / 3600
    rows.append({"dataset": name, "lignes": len(d), "UE": d.ue_id.nunique(), "UE-heures": round(ue_h, 1),
                 "handovers/UE-h": round(d.handover.sum() / ue_h, 1),
                 "debit med (Mbit/s)": round(d.throughput_mbps.median(), 2),
                 "latence med (ms)": round(d.latency_ms.median(), 1),
                 "latence p95 (ms)": round(d.latency_ms.quantile(0.95), 1),
                 "pertes moy (%)": round(d.loss_pct.mean(), 2),
                 "charge moy (%)": round(d.load_pct.mean(), 1),
                 "vitesse moy (m/s)": round(d.speed.mean(), 1),
                 "% non-normal": round(100 * (d.label != "normal").mean(), 1)})
res = pd.DataFrame(rows).set_index("dataset").T
res.to_csv("data/processed/datasets_comparison.csv")
print(res.to_string())

fig, ax = plt.subplots(1, 3, figsize=(13, 4))
for a, col, ttl in zip(ax, ["latency_ms", "throughput_mbps", "load_pct"],
                       ["Latence (ms, log)", "Débit (Mbit/s, log)", "Charge (%)"]):
    a.boxplot([data[n][col].clip(lower=1e-3) for n in DS], showfliers=False)
    a.set_xticks([1, 2, 3]); a.set_xticklabels(["v1", "SUMO", "NTN"])
    a.set_title(ttl)
    if col != "load_pct": a.set_yscale("log")
plt.tight_layout(); plt.savefig("figures/14_comparaison_datasets.png", dpi=150)

# avant/apres nettoyage : brut contre traite (colonnes *_norm)
raw = pd.read_csv("data/raw/dataset_6g_raw.csv"); pro = pd.read_csv("data/processed/dataset_6g.csv")
print("\nAvant/apres nettoyage (v1) : lignes %d -> %d ; NaN %d -> %d ; doublons %d -> %d" % (
    len(raw), len(pro), raw.isna().sum().sum(), pro.isna().sum().sum(),
    raw.duplicated(["timestamp", "ue_id"]).sum(), pro.duplicated(["timestamp", "ue_id"]).sum()))
print("Moyenne / ecart-type des colonnes normalisees :")
print(pro[[c for c in pro.columns if c.endswith("_norm")]].agg(["mean", "std"]).round(3).T.to_string())
