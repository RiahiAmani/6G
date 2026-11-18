import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.expanduser("~/6G/a-infra/a10-continuum/results")
tag = sys.argv[1] if len(sys.argv) > 1 else "netem"
d = pd.read_csv(f"{R}/results_{tag}.csv")
d["total_ms"] = d["total"] * 1000
d["connect_ms"] = d["connect"] * 1000
order = [t for t in ("ue", "edge", "fog", "cloud") if t in d.tier.unique()]
remote = [t for t in ("edge", "fog", "cloud") if t in order]
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 300)

print("== Toutes les requêtes : nombre, moyenne, écart-type (ms)")
print(d.groupby(["n", "tier"])[["connect_ms", "proc_ms", "total_ms"]].agg(["count", "mean", "std"]).round(1))
print("\n== Temps total : moyenne et écart-type entre les séries (une moyenne par série)")
print(d.groupby(["n", "tier", "serie"])["total_ms"].mean().groupby(["n", "tier"]).agg(["count", "mean", "std"]).round(1))
m = d.groupby(["n", "tier"])["total_ms"].mean().unstack()[order]
print("\n== Temps total moyen (ms)"); print(m.round(1))
print("\n== Meilleur tier par taille, UE compris :"); print(m.idxmin(axis=1).to_string())
print("\n== Meilleur tier par taille, Edge/Fog/Cloud seulement :"); print(m[remote].idxmin(axis=1).to_string())

def crossing(a, b):
    diff = (m[a] - m[b]).dropna(); ns = diff.index.values.astype(float)
    if diff.iloc[0] > 0: return "dès la plus petite taille (n=%d)" % ns[0]
    for i in range(1, len(ns)):
        if diff.iloc[i-1] <= 0 < diff.iloc[i]:
            x0, x1 = np.log(ns[i-1]), np.log(ns[i]); y0, y1 = diff.iloc[i-1], diff.iloc[i]
            return "n ≈ %d" % round(np.exp(x0 - y0 * (x1 - x0) / (y1 - y0)))
    return "non atteint sur la plage mesurée"
print()
for a, b in (("edge", "fog"), ("edge", "cloud"), ("fog", "cloud")):
    if a in m and b in m: print(f"point de bascule : {b} devient meilleur que {a} : {crossing(a, b)}")

fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
for t in order:
    g = d[d.tier == t].groupby("n")
    for k, col in ((0, "proc_ms"), (1, "total_ms")):
        mu, sd = g[col].mean(), g[col].std()
        ax[k].errorbar(mu.index, mu.values, yerr=sd.values, marker="o", capsize=2, label=t)
for k, title in ((0, "Temps de traitement (ms)"), (1, "Temps total vu par l'UE (ms)")):
    ax[k].set_xscale("log"); ax[k].set_yscale("log"); ax[k].set_xlabel("taille de la tâche n")
    ax[k].set_title(title); ax[k].legend(); ax[k].grid(True, which="both", alpha=.3)
net = d[d.tier.isin(remote)].groupby("tier")["connect_ms"].agg(["mean", "std"]).reindex(remote)
ax[2].bar(net.index, net["mean"], yerr=net["std"], capsize=4)
ax[2].set_title("Temps de connexion TCP (ms)"); ax[2].grid(True, axis="y", alpha=.3)
plt.tight_layout(); out = f"{R}/a10_{tag}.png"; plt.savefig(out, dpi=130); print("\nfigure :", out)
