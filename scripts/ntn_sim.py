import numpy as np
import pandas as pd
from skyfield.api import load, wgs84

C = 299792.458                        # km/s
OBS = wgs84.latlon(36.8065, 10.1815)  # station (Tunis)
MIN_ELEV, N_SATS = 25.0, 500
ALT_MIN, ALT_MAX = 450.0, 620.0       # coques opérationnelles (hypothèse)

ts = load.timescale()
allsats = load.tle_file("ntn/starlink.tle")          # fichier local déjà téléchargé
t0_tt = max(s.epoch.tt for s in allsats)             # instant fixe = TLE le plus récent
t = ts.tt_jd(t0_tt + np.arange(0, 1, 30 / 86400))    # 24 h, pas de 30 s
t_ref = ts.tt_jd(t0_tt)

alt = np.array([wgs84.height_of(s.at(t_ref)).km for s in allsats])
print("Altitudes (km), percentiles 0/5/50/95/100 :", np.percentile(alt, [0, 5, 50, 95, 100]).round(0))
ok = [s for s, h in zip(allsats, alt) if ALT_MIN <= h <= ALT_MAX]
print(f"{len(ok)} satellites retenus sur {len(allsats)}")
n = min(N_SATS, len(ok))

rows = []
for seed in (1, 2, 3):
    rng = np.random.default_rng(seed)
    sats = [ok[i] for i in rng.choice(len(ok), n, replace=False)]
    elev = np.empty((n, len(t))); dist = np.empty_like(elev)
    for i, s in enumerate(sats):
        a, _, d = (s - OBS).at(t).altaz()
        elev[i], dist[i] = a.degrees, d.km
    vis = elev >= MIN_ELEV
    best = np.where(vis, dist, np.inf).min(axis=0)
    cov = np.isfinite(best)
    delay = best[cov] / C * 1000
    rows.append(dict(seed=seed, coverage_pct=100 * cov.mean(),
                     n_vis_mean=vis.sum(0).mean(), n_vis_max=int(vis.sum(0).max()),
                     leo_delay_mean_ms=delay.mean(), leo_delay_min_ms=delay.min(),
                     leo_delay_max_ms=delay.max()))
    if seed == 1:
        pd.DataFrame({"t_s": np.arange(len(t)) * 30, "n_visible": vis.sum(0),
                      "delay_leo_ms": np.where(cov, best / C * 1000, np.nan)}) \
          .to_csv("data/processed/ntn_leo_timeline.csv", index=False)

res = pd.DataFrame(rows)
res.to_csv("data/processed/ntn_results.csv", index=False)
print(res.drop(columns="seed").agg(["mean", "std"]).round(2).T)

R, H = 6371.0, 35786.0
gamma = np.radians(36.8065)
d_geo = np.sqrt(R**2 + (R + H)**2 - 2 * R * (R + H) * np.cos(gamma))
print(f"GEO aller simple : {d_geo / C * 1000:.1f} ms | RTT x4 : {4 * d_geo / C * 1000:.0f} ms")
print(f"LEO RTT x4 (moyenne des 3 tirages) : {4 * res.leo_delay_mean_ms.mean():.1f} ms")
