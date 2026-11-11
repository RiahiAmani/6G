import glob, re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

RSU = np.array([400.0, 400.0])                 # unité de bord de route au centre de la grille
V2V_RANGE, V2I_RANGE = 300.0, 250.0            # portées (m)
D50_V2V, W_V2V = 150.0, 35.0                   # distance à 50 % de réception, pente
D50_V2I, W_V2I = 140.0, 30.0
ALPHA = 0.03                                   # perte par collision, par voisin

def pdr_dist(d, d50, w):
    return 1.0 / (1.0 + np.exp((d - d50) / w))

def load(fcd):
    rows = []
    for _, el in ET.iterparse(fcd, events=("end",)):
        if el.tag == "timestep":
            t = float(el.get("time"))
            for v in el.findall("vehicle"):
                rows.append((t, v.get("id"), float(v.get("x")), float(v.get("y")), float(v.get("speed"))))
            el.clear()
    return pd.DataFrame(rows, columns=["t", "veh", "x", "y", "speed"])

results = []
for f in sorted(glob.glob("sumo/runs/*.fcd.xml")):
    m = re.search(r"p(\d+)_s(\d+)", f)
    p, s = int(m[1]), int(m[2])
    df = load(f)
    active = df.groupby("t").size().mean()
    nn, iso, pdr_v, lat_v, cov, pdr_i, lat_i = [], [], [], [], [], [], []
    for t, g in df.groupby("t"):
        xy = g[["x", "y"]].to_numpy()
        n = len(xy)
        if n < 2:
            continue
        D = np.linalg.norm(xy[:, None] - xy[None], axis=2)
        np.fill_diagonal(D, np.inf)
        mask = D <= V2V_RANGE
        k = mask.sum(1)
        nn.extend(k); iso.extend(k == 0)
        for i in range(n):
            if k[i] > 0:
                pdr_v.append(pdr_dist(D[i, mask[i]], D50_V2V, W_V2V).mean() * np.exp(-ALPHA * k[i]))
                lat_v.append(2.0 + 0.15 * k[i])
        d = np.linalg.norm(xy - RSU, axis=1)
        c = d <= V2I_RANGE
        cov.extend(c)
        nc = int(c.sum())
        if nc > 0:
            pdr_i.extend(pdr_dist(d[c], D50_V2I, W_V2I) * np.exp(-ALPHA * nc))
            lat_i.extend([8.0 + 0.4 * nc] * nc)
    results.append(dict(period_s=p, seed=s, active_veh=round(active, 1),
        neighbors=np.mean(nn), isolated_pct=100 * np.mean(iso),
        v2v_pdr=100 * np.mean(pdr_v), v2v_lat_ms=np.mean(lat_v),
        v2i_cov_pct=100 * np.mean(cov), v2i_pdr=100 * np.mean(pdr_i), v2i_lat_ms=np.mean(lat_i)))

res = pd.DataFrame(results)
res.to_csv("data/processed/v2x_results.csv", index=False)
print(res.groupby("period_s").agg(["mean", "std"]).round(2).T)
