import glob, re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_fscore_support

CELLS = np.array([(200, 200), (600, 200), (200, 600), (600, 600)], dtype=float)
H = 5                                   # historique et horizon (s)

def nearest(x, y):
    d = np.stack([np.hypot(x - cx, y - cy) for cx, cy in CELLS], axis=1)
    return d.argmin(axis=1), d

frames = []
for f in sorted(glob.glob("sumo/runs/*.fcd.xml")):
    run = re.search(r"p\d+_s\d+", f)[0]
    rows = []
    for _, el in ET.iterparse(f, events=("end",)):
        if el.tag == "timestep":
            t = float(el.get("time"))
            for v in el.findall("vehicle"):
                rows.append((t, run + "_" + v.get("id"), float(v.get("x")),
                             float(v.get("y")), float(v.get("speed"))))
            el.clear()
    frames.append(pd.DataFrame(rows, columns=["t", "veh", "x", "y", "speed"]))
df = pd.concat(frames, ignore_index=True).sort_values(["veh", "t"]).reset_index(drop=True)

g = df.groupby("veh")
df["x_past"], df["y_past"], df["t_past"] = g["x"].shift(H), g["y"].shift(H), g["t"].shift(H)
df["x_fut"], df["y_fut"], df["t_fut"] = g["x"].shift(-H), g["y"].shift(-H), g["t"].shift(-H)
# on ne garde que les lignes où le véhicule existe sans trou à t-5 et t+5
df = df[(df.t - df.t_past == H) & (df.t_fut - df.t == H)].reset_index(drop=True)

df["cur"], dist = nearest(df.x.values, df.y.values)
df["tgt"], _ = nearest(df.x_fut.values, df.y_fut.values)
df["dx"], df["dy"] = df.x - df.x_past, df.y - df.y_past
for k in range(4):
    df[f"d{k}"] = dist[:, k]
df["extrap"], _ = nearest((df.x + df.dx).values, (df.y + df.dy).values)

FEATS = ["x", "y", "dx", "dy", "speed", "cur", "d0", "d1", "d2", "d3"]
change = (df.tgt != df.cur).values
print(f"{len(df)} exemples, {df.veh.nunique()} véhicules, "
      f"changement de cellule dans {H} s : {100 * change.mean():.1f} %")

def score(name, pred, idx):
    yt, yp = change[idx], pred != df.cur.values[idx]
    p, r, f1, _ = precision_recall_fscore_support(yt, yp, average="binary", zero_division=0)
    return dict(method=name, accuracy=np.mean(pred == df.tgt.values[idx]),
                precision=p, recall=r, f1=f1)

res = []
for fold, (tr, te) in enumerate(GroupKFold(n_splits=5).split(df, groups=df.veh)):
    res.append(dict(fold=fold, **score("persistance", df.cur.values[te], te)))
    res.append(dict(fold=fold, **score("extrapolation", df.extrap.values[te], te)))
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=2, random_state=42)
    rf.fit(df.loc[tr, FEATS], df.tgt.values[tr])
    res.append(dict(fold=fold, **score("random_forest", rf.predict(df.loc[te, FEATS]), te)))

res = pd.DataFrame(res)
res.to_csv("data/processed/mobility_prediction_results.csv", index=False)
print(res.groupby("method")[["accuracy", "precision", "recall", "f1"]]
        .agg(["mean", "std"]).round(3).T)
