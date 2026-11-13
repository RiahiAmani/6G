import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CAP, BOOST, HOLD = 31, 0.30, 10
df = pd.read_csv("data/processed/load_samples.csv")

def policy(col, thr):
    cong = boosted = 0
    for _, g in df.groupby(["run", "cell"]):
        trig = (g[col].values >= thr).astype(float)
        b = pd.Series(trig).rolling(HOLD, min_periods=1).max().values
        cong += int((100 * g.n_fut.values / (CAP * (1 + BOOST * b)) >= 85).sum())
        boosted += int(b.sum())
    return cong, boosted

rows = []
for col in ("persistance", "tendance", "random_forest"):
    for thr in range(60, 96, 5):
        c, b = policy(col, thr)
        rows.append(dict(methode=col, seuil=thr, secondes_congestion=c, secondes_capacite=b))
out = pd.DataFrame(rows)
out.to_csv("data/processed/load_policy_sweep.csv", index=False)
print(out.to_string(index=False))

for m, g in out.groupby("methode"):
    plt.plot(g.secondes_capacite, g.secondes_congestion, marker="o", label=m)
plt.xlabel("Secondes de capacité ajoutée (coût)")
plt.ylabel("Secondes de congestion restantes")
plt.title("Compromis coût / congestion selon le seuil de déclenchement")
plt.legend(); plt.tight_layout()
plt.savefig("figures/24_politiques.png", dpi=150)
