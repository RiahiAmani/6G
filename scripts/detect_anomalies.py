import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_fscore_support

df = pd.read_csv("data/processed/dataset_6g.csv")
F = ["throughput_mbps", "latency_ms", "jitter_ms", "loss_pct", "load_pct"]
y = (df.label != "normal").values
rows = []
for fold, (tr, te) in enumerate(GroupKFold(n_splits=5).split(df, groups=df.ue_id)):
    mu = df.iloc[tr].groupby("ue_type")[F].mean()
    sd = df.iloc[tr].groupby("ue_type")[F].std()
    Z = (df[F].values - mu.loc[df.ue_type].values) / sd.loc[df.ue_type].values
    preds = {"regle_3sigma": (np.abs(Z[te]) > 3).any(axis=1)}
    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42, n_jobs=2)
    iso.fit(Z[tr])
    preds["isolation_forest"] = iso.predict(Z[te]) == -1
    lab = df.label.values[te]
    for m, p in preds.items():
        pr, rc, f1, _ = precision_recall_fscore_support(y[te], p, average="binary", zero_division=0)
        rows.append(dict(fold=fold, method=m, precision=pr, recall=rc, f1=f1,
                         recall_anomaly=p[lab == "anomaly"].mean(),
                         recall_congestion=p[lab == "congestion"].mean(),
                         false_alarm=p[lab == "normal"].mean()))
res = pd.DataFrame(rows)
res.to_csv("data/processed/anomaly_results.csv", index=False)
print(res.drop(columns="fold").groupby("method").agg(["mean", "std"]).round(3).T)
