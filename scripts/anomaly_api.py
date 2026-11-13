import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

F = ["throughput_mbps", "latency_ms", "jitter_ms", "loss_pct", "load_pct"]
MODEL = "data/processed/anomaly_model.joblib"

def train(df):
    mu = df.groupby("ue_type")[F].mean()
    sd = df.groupby("ue_type")[F].std()
    Z = (df[F].values - mu.loc[df.ue_type].values) / sd.loc[df.ue_type].values
    iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42, n_jobs=2).fit(Z)
    raw = -iso.score_samples(Z)                      # plus grand = plus anormal
    bundle = dict(iso=iso, mu=mu, sd=sd, lo=raw.min(), hi=raw.max())
    joblib.dump(bundle, MODEL)
    return bundle

def score_rows(df, bundle=None):
    """df : colonnes du schéma v1.0 (timestamp, ue_id, ue_type + 5 métriques)."""
    b = bundle or joblib.load(MODEL)
    Z = (df[F].values - b["mu"].loc[df.ue_type].values) / b["sd"].loc[df.ue_type].values
    raw = -b["iso"].score_samples(Z)
    score = np.clip((raw - b["lo"]) / (b["hi"] - b["lo"]), 0, 1)
    return pd.DataFrame(dict(timestamp=df.timestamp.values, ue_id=df.ue_id.values,
                             score=score.round(4),
                             is_anomaly=(b["iso"].predict(Z) == -1),
                             method="isolation_forest"))

if __name__ == "__main__":
    df = pd.read_csv("data/processed/dataset_6g.csv")
    out = score_rows(df, train(df))
    with open("data/processed/anomaly_scores.jsonl", "w") as f:
        for r in out.to_dict("records"):
            f.write(json.dumps(r) + "\n")
    print(out.is_anomaly.mean().round(3), "des lignes signalées")
    print(out.head(3).to_json(orient="records", indent=1))
