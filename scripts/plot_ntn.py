import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

tl = pd.read_csv("data/processed/ntn_leo_timeline.csv")
res = pd.read_csv("data/processed/ntn_results.csv")
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot(tl.t_s / 3600, tl.n_visible)
ax[0].set_title("Satellites visibles (>= 25°)"); ax[0].set_xlabel("heures"); ax[0].set_ylabel("nombre")
ax[1].plot(tl.t_s / 3600, tl.delay_leo_ms, lw=0.8)
ax[1].set_title("Délai LEO aller simple (sat. le plus proche)"); ax[1].set_xlabel("heures"); ax[1].set_ylabel("ms")
rtt = {"LEO": 4 * res.leo_delay_mean_ms.mean(), "GEO": 4 * 124.3}
ax[2].bar(rtt.keys(), rtt.values(), yerr=[4 * res.leo_delay_mean_ms.std(), 0], capsize=4)
ax[2].axhline(5, color="r", ls="--", label="latence profil URLLC du dataset (5 ms)")
ax[2].set_yscale("log"); ax[2].set_ylabel("ms"); ax[2].set_title("RTT, propagation seule (log)"); ax[2].legend()
plt.tight_layout(); plt.savefig("figures/17_ntn.png", dpi=150); print("OK")
