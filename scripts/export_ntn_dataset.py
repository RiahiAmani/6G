import numpy as np
import pandas as pd
from skyfield.api import load, wgs84

C = 299792.458
OBS = wgs84.latlon(36.8065, 10.1815)
MIN_ELEV, N_SATS = 25.0, 500
ALT_MIN, ALT_MAX = 450.0, 620.0
N_UE, STEP, DUR = 10, 30, 86400          # 10 UE fixes (zone rurale), pas de 30 s, 24 h
rng = np.random.default_rng(42)

ts = load.timescale()
allsats = load.tle_file("ntn/starlink.tle")
t0_tt = max(s.epoch.tt for s in allsats)
t = ts.tt_jd(t0_tt + np.arange(0, DUR, STEP) / 86400)
t_ref = ts.tt_jd(t0_tt)

alt = np.array([wgs84.height_of(s.at(t_ref)).km for s in allsats])
ok = [s for s, h in zip(allsats, alt) if ALT_MIN <= h <= ALT_MAX]
r1 = np.random.default_rng(1)
sats = [ok[i] for i in r1.choice(len(ok), N_SATS, replace=False)]

elev = np.empty((N_SATS, len(t))); dist = np.empty_like(elev)
for i, s in enumerate(sats):
    a, _, d = (s - OBS).at(t).altaz()
    elev[i], dist[i] = a.degrees, d.km
dist_vis = np.where(elev >= MIN_ELEV, dist, np.inf)
idx = dist_vis.argmin(axis=0)
best = dist_vis.min(axis=0)
cov = np.isfinite(best)
names = np.array([s.name.replace(" ", "_") for s in sats])

serving = np.where(cov, names[idx], "none")
delay = np.where(cov, best / C * 1000, np.nan)
ho = np.zeros(len(t), dtype=int)
ho[1:] = ((serving[1:] != serving[:-1]) & cov[1:] & cov[:-1]).astype(int)

rows = []
for u in range(N_UE):
    ue_id = f"rural_{u+1:02d}"
    n = len(t)
    lat_ms = 4 * delay + rng.normal(15, 2, n)        # RTT propagation + traitement supposé 15 ms
    rows.append(pd.DataFrame(dict(
        timestamp=np.arange(n) * float(STEP), ue_id=ue_id, ue_type="mmtc", slice="mmtc",
        cell_id=serving, x=0.0, y=0.0, speed=0.0,
        throughput_mbps=np.where(cov, np.clip(rng.normal(20, 3, n), 0, None), 0.0),
        latency_ms=lat_ms,
        jitter_ms=np.clip(rng.normal(3, 0.5, n), 0.01, None),
        loss_pct=np.where(cov, np.clip(rng.normal(0.5, 0.2, n), 0, None), 100.0),
        load_pct=np.clip(rng.normal(40, 8, n), 0, 100),
        handover=ho, label=np.where(cov, "normal", "anomaly"))))
df = pd.concat(rows, ignore_index=True).round(3)
df.to_csv("data/processed/dataset_6g_ntn.csv", index=False)
print(df.shape)
print("Couverture :", round(100 * cov.mean(), 1), "%")
print("Handovers satellite par UE :", int(ho.sum()), "| satellites distincts :", len(set(serving) - {"none"}))
print("Intervalle moyen entre handovers :", round(DUR / max(ho.sum(), 1) / 60, 1), "min")
