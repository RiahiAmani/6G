"""Atelier 25 (v2) : detection sur dataset a EPISODES. Evaluation par ligne ET par episode,
selon l'intensite, avec metriques independantes du seuil (AUC, precision moyenne)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, average_precision_score

F = ["throughput_mbps", "latency_ms", "jitter_ms", "loss_pct", "load_pct"]
W = 5                       # fenetre causale (s) pour les variables de contexte temporel
df = pd.read_csv("data/processed/dataset_6g_episodes.csv").sort_values(["ue_id", "timestamp"]).reset_index(drop=True)
epi = pd.read_csv("data/processed/episodes_rows.csv")
meta = pd.read_csv("data/processed/episodes_meta.csv")
df = df.merge(epi, on=["timestamp", "ue_id"], how="left")
df["episode_id"] = df.episode_id.fillna(-1).astype(int)
y = (df.label != "normal").values
prev = y.mean()
CONT = round(prev, 2)       # contamination = prevalence reelle (avantage irrealiste, voir limites)
print(f"{len(df)} lignes, prevalence anormale {100*prev:.1f} %, contamination utilisee {CONT}")

names = ["regle_3sigma", "iforest_instant", "iforest_fenetre"]
pred = {m: np.zeros(len(df), bool) for m in names}
score = {m: np.zeros(len(df)) for m in names}
for tr, te in GroupKFold(n_splits=5).split(df, groups=df.ue_id):
    mu = df.iloc[tr].groupby("ue_type")[F].mean(); sd = df.iloc[tr].groupby("ue_type")[F].std()
    Z = (df[F].values - mu.loc[df.ue_type].values) / sd.loc[df.ue_type].values
    Zr = pd.DataFrame(Z, columns=F).assign(ue=df.ue_id.values) \
           .groupby("ue")[F].transform(lambda s: s.rolling(W, min_periods=1).mean()).values
    Xw = np.hstack([Z, Zr])
    pred["regle_3sigma"][te] = (np.abs(Z[te]) > 3).any(axis=1)
    score["regle_3sigma"][te] = np.abs(Z[te]).max(axis=1)
    for m, X in (("iforest_instant", Z), ("iforest_fenetre", Xw)):
        iso = IsolationForest(n_estimators=200, contamination=CONT, random_state=42, n_jobs=2).fit(X[tr])
        pred[m][te] = iso.predict(X[te]) == -1
        score[m][te] = -iso.score_samples(X[te])

rows = []
for m in names:
    p, s = pred[m], score[m]
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
    r = dict(methode=m, precision=pr, rappel=rc, f1=f1, auc=roc_auc_score(y, s),
             prec_moy=average_precision_score(y, s), fausses_alertes=p[~y].mean())
    for k in ("faible", "moyenne", "forte"):
        mask = (df.intensite == k).values
        r[f"rappel_att_{k}"] = p[mask].mean() if mask.any() else np.nan
    r["rappel_congestion"] = p[(df.label == "congestion").values].mean()
    # niveau episode : detecte si au moins une alerte dans l'episode ; delai = 1re alerte - debut
    det, delay = [], []
    for _, e in meta.iterrows():
        sel = (df.episode_id == e.episode_id).values
        ts = df.timestamp.values[sel & p]
        det.append(len(ts) > 0)
        if len(ts): delay.append(ts.min() - e.t_start)
    r["episodes_detectes"] = f"{sum(det)}/{len(det)}"
    r["delai_median_s"] = np.median(delay) if delay else np.nan
    rows.append(r)
res = pd.DataFrame(rows)
res.to_csv("data/processed/anomaly_episodes_results.csv", index=False)
print(res.round(3).T.to_string(header=False))
