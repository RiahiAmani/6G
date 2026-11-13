import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/mobility_prediction_results.csv")
g = df.groupby("method")[["accuracy", "precision", "recall", "f1"]].agg(["mean", "std"])
m = g.xs("mean", axis=1, level=1)
s = g.xs("std", axis=1, level=1)
m.plot(kind="bar", yerr=s, capsize=3, figsize=(8, 4),
       title="Prédiction de la cellule à 5 s (moyenne ± écart-type, 5 plis)")
plt.ylabel("score"); plt.xticks(rotation=0); plt.tight_layout()
plt.savefig("figures/18_prediction_mobilite.png", dpi=150)
print("OK")
