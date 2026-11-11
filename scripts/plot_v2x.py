import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/v2x_results.csv")
g = df.groupby("period_s").agg(["mean", "std"])
g = g.sort_values(("active_veh", "mean"))
x = g[("active_veh", "mean")]

def curve(ax, cols, labels, title, ylabel):
    for c, l in zip(cols, labels):
        ax.errorbar(x, g[(c, "mean")], yerr=g[(c, "std")], marker="o", capsize=3, label=l)
    ax.set_title(title); ax.set_xlabel("Véhicules actifs (moyenne)"); ax.set_ylabel(ylabel)
    ax.legend()

fig, ax = plt.subplots(2, 2, figsize=(11, 8))
curve(ax[0, 0], ["neighbors"], ["voisins V2V"], "Voisins dans la portée (mesuré)", "nombre")
curve(ax[0, 1], ["isolated_pct", "v2i_cov_pct"], ["véhicules isolés", "couverture RSU"],
      "Isolement et couverture (mesuré)", "%")
curve(ax[1, 0], ["v2v_pdr", "v2i_pdr"], ["V2V", "V2I"], "PDR relatif (modèle)", "%")
curve(ax[1, 1], ["v2v_lat_ms", "v2i_lat_ms"], ["V2V", "V2I"], "Latence (modèle)", "ms")
plt.tight_layout()
plt.savefig("figures/16_v2x_densite.png", dpi=150)
print("OK")
