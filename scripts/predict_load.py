import glob, re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_fscore_support

CELLS = np.array([(200, 200), (600, 200), (200, 600), (600, 600)], dtype=float)
CAP, H, T0, THR = 31, 10, 60, 85.0
BOOST, HOLD = 0.30, 10          # +30 % de capacité pendant 10 s (hypothèses)

rows = []
for f in sorted(glob.glob("sumo/runs/p1_s*.fcd.xml")):
    run = re.search(r"p\d+_s\d+", f)[0]
    for _, el in ET.iterparse(f, events=("end",)):
        if el.tag == "timestep":
            t = float(el.get("time"))
            xy = np.array([(float(v.get("x")), float(v.get("y"))) for v in el.findall("vehicle")])
            c = (np.stack([np.hypot(xy[:, 0] - a, xy[:, 1] - b) for a, b in CELLS], 1).argmin(1)
                 if len(xy) else np.array([], dtype=int))
            for k in range(4):
                rows.append((run, int(t), k, int((c == k).sum())))
            el.clear()
d = pd.DataFrame(rows, columns=["run", "t", "cell", "n"])

samples = []
for (run, cell), g in d.groupby(["run", "cell"]):
    s = g.set_index("t").n.reindex(np.arange(0, g.t.max() + 1)).fillna(0).values
    L = 100 * s / CAP
    for t in range(T0, len(s) - H):
        samples.append(dict(run=run, cell=cell, t=t, l0=L[t], l1=L[t-1], l2=L[t-2],
                            l5=L[t-5], l10=L[t-10], y=L[t+H], n_fut=s[t+H]))
df = pd.DataFrame(samples)
df["slope"] = (df.l0 - df.l10) / 10
df["persistance"] = df.l0
df["tendance"] = df.l0 + df.slope * H
FEATS = ["l0", "l1", "l2", "l5", "l10", "slope"]
print(f"{len(df)} échantillons, {df.run.nunique()} simulations, "
      f"congestion à t+{H}s : {100 * (df.y >= THR).mean():.1f} %")

df["random_forest"] = np.nan
res = []
for fold, (tr, te) in enumerate(GroupKFold(n_splits=3).split(df, groups=df.run)):
    rf = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=5,
                               n_jobs=2, random_state=42)
    rf.fit(df.loc[tr, FEATS], df.y.values[tr])
    df.loc[df.index[te], "random_forest"] = rf.predict(df.loc[te, FEATS])
    for m in ("persistance", "tendance", "random_forest"):
        p = df[m].values[te]; y = df.y.values[te]
        pr, rc, f1, _ = precision_recall_fscore_support(y >= THR, p >= THR,
                                                        average="binary", zero_division=0)
        res.append(dict(fold=fold, method=m, mae=np.abs(p - y).mean(),
                        rmse=np.sqrt(((p - y) ** 2).mean()),
                        precision=pr, recall=rc, f1=f1))
res = pd.DataFrame(res)
res.to_csv("data/processed/load_prediction_results.csv", index=False)
print(res.groupby("method")[["mae", "rmse", "precision", "recall", "f1"]]
        .agg(["mean", "std"]).round(3).T)

# Réactif / prédictif : décision à t, capacité supplémentaire effective à partir de t+10
pol = []
for name, col in [("aucune action", None), ("réactive (persistance)", "persistance"),
                  ("prédictive (tendance)", "tendance"), ("prédictive (random forest)", "random_forest")]:
    cong = boosted = 0
    for _, g in df.groupby(["run", "cell"]):
        if col is None:
            b = np.zeros(len(g))
        else:
            trig = (g[col].values >= THR).astype(float)
            b = pd.Series(trig).rolling(HOLD, min_periods=1).max().values
        cap_eff = CAP * (1 + BOOST * b)
        cong += int((100 * g.n_fut.values / cap_eff >= THR).sum())
        boosted += int(b.sum())
    pol.append(dict(politique=name, secondes_congestion=cong, secondes_capacite_ajoutee=boosted))
pol = pd.DataFrame(pol)
pol["congestion_evitee_%"] = (100 * (1 - pol.secondes_congestion / pol.secondes_congestion[0])).round(1)
pol.to_csv("data/processed/load_policy_results.csv", index=False)
print(pol.to_string(index=False))
df.to_csv("data/processed/load_samples.csv", index=False)
