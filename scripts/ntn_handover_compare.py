import numpy as np
import pandas as pd
from skyfield.api import load, wgs84

C = 299792.458
OBS = wgs84.latlon(36.8065, 10.1815)
MIN_ELEV, N_SATS = 25.0, 500
ALT_MIN, ALT_MAX = 450.0, 620.0
STEP, DUR = 30, 86400

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

vis = elev >= MIN_ELEV
dist_vis = np.where(vis, dist, np.inf)
idx = dist_vis.argmin(axis=0)
cov = np.isfinite(dist_vis.min(axis=0))

def stats(serving):
    """serving : liste d'indices de satellites (ou None si coupure)."""
    ho = sum(1 for a, b in zip(serving[:-1], serving[1:])
             if a is not None and b is not None and a != b)
    delays = [dist[s, k] / C * 1000 for k, s in enumerate(serving) if s is not None]
    return ho, float(np.mean(delays))

# Stratégie 1 : satellite le plus proche à chaque pas
s1 = [int(idx[k]) if cov[k] else None for k in range(len(t))]

# Stratégie 2 : garder le satellite servant tant qu'il est visible
s2, cur = [], None
for k in range(len(t)):
    if cur is not None and vis[cur, k]:
        s2.append(cur)
        continue
    cur = int(idx[k]) if cov[k] else None
    s2.append(cur)

h1, d1 = stats(s1)
h2, d2 = stats(s2)
print(f"{'Stratégie':<28}{'Handovers/24h':>15}{'Délai moyen (ms)':>20}")
print(f"{'plus proche':<28}{h1:>15}{d1:>20.2f}")
print(f"{'garder tant que visible':<28}{h2:>15}{d2:>20.2f}")
print(f"Réduction des handovers : {100 * (1 - h2 / h1):.0f} %")
print(f"Couverture stratégie 2 : {100 * np.mean([s is not None for s in s2]):.1f} %")
