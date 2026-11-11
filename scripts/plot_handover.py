import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/handover_results.csv")
g = df.groupby(["speed", "strategy"])[["handovers", "pingpongs"]].agg(["mean", "std"])

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for k, metric in enumerate(["handovers", "pingpongs"]):
    m = g[metric]["mean"].unstack()
    s = g[metric]["std"].unstack()
    m.plot(kind="bar", yerr=s, ax=ax[k], capsize=3, title=f"{metric} (moyenne ± écart-type)")
    ax[k].set_xlabel("Vitesse (m/s)")
plt.tight_layout()
plt.savefig("figures/15_handover_comparaison.png", dpi=150)
print("OK")
