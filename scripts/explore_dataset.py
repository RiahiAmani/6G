import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/dataset_6g.csv")

# Répartition des labels
df["label"].value_counts().plot(kind="bar", title="Répartition des étiquettes")
plt.ylabel("Nombre d'échantillons"); plt.tight_layout()
plt.savefig("figures/14_labels.png", dpi=150); plt.clf()

# Latence par type d'UE
df.boxplot(column="latency_ms", by="ue_type")
plt.title("Latence par type d'UE"); plt.suptitle(""); plt.ylabel("ms")
plt.savefig("figures/14_latence_par_type.png", dpi=150); plt.clf()

# Débit par type d'UE (échelle log car très différents)
df.boxplot(column="throughput_mbps", by="ue_type")
plt.yscale("log"); plt.title("Débit par type d'UE"); plt.suptitle("")
plt.savefig("figures/14_debit_par_type.png", dpi=150); plt.clf()

# Trajectoire d'un UE
u = df[df["ue_id"] == "ue_001"]
plt.plot(u["x"], u["y"]); plt.title("Trajectoire de ue_001")
plt.xlabel("x (m)"); plt.ylabel("y (m)")
plt.savefig("figures/14_trajectoire.png", dpi=150); plt.clf()

# Matrice de corrélation
corr = df[["throughput_mbps", "latency_ms", "jitter_ms", "loss_pct", "load_pct"]].corr()
plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
plt.xticks(range(5), corr.columns, rotation=45, ha="right")
plt.yticks(range(5), corr.columns); plt.colorbar()
plt.title("Corrélations"); plt.tight_layout()
plt.savefig("figures/14_correlations.png", dpi=150)
print("Figures enregistrées dans figures/")
