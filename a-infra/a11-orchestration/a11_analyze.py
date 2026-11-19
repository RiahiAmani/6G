import glob, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.expanduser("~/6G/a-infra/a11-orchestration/results")
OFF = float(os.environ.get("OFFSET", 0))      # secondes à ajouter aux heures de vm-k8s (décalage d'horloge)
SS = 100                                      # « régime établi » : les SS dernières secondes de la charge
SERV = ["urllc", "embb", "mmtc"]
pd.set_option("display.width", 220)

def rd(name, **kw):
    f = os.path.join(R, name)
    return pd.read_csv(f, **kw) if os.path.exists(f) else None

runs, rows = {}, []
for f in sorted(glob.glob(os.path.join(R, "meta_*.txt"))):
    tag = os.path.basename(f)[5:-4]
    m = dict(l.strip().split("=") for l in open(f))
    t0, t1 = float(m["load_start"]), float(m["load_end"])
    ld = rd(f"load_{tag}.csv", dtype={"code": str}); ld["ok"] = ld.code == "200"
    ev = rd(f"events_{tag}.csv")
    if ev is None: ev = pd.DataFrame(columns=["timestamp", "service", "from_tier", "to_tier"])
    ev["t"] = ev.timestamp + OFF
    ti = rd(f"tiers_{tag}.csv")
    if ti is not None: ti["t"] = ti.timestamp + OFF
    pr = {}
    for s in SERV:
        p = rd(f"probe_{tag}_{s}.csv", dtype={"code": str})
        if p is not None: p["ok"] = p.code == "200"; pr[s] = p
    runs[tag] = dict(mode=tag.split("_")[0], t0=t0, t1=t1, ld=ld.sort_values("t_fin"), ev=ev, ti=ti)

    ok = ld[ld.ok]
    w = ok[(ok.t_fin >= t0) & (ok.t_fin <= t1)]
    ss = ok[(ok.t_fin >= t1 - SS) & (ok.t_fin <= t1)]
    allw = ld[(ld.t_fin >= t0) & (ld.t_fin <= t1)]
    mv = ev[(ev.service == "urllc") & (ev.from_tier == "edge") & (ev.t > t0)]
    bk = ev[(ev.service == "urllc") & (ev.to_tier == "edge") & (ev.t > t1)]
    row = dict(tag=tag, mode=runs[tag]["mode"],
               req_s=len(w) / (t1 - t0), mean_s=w.total_s.mean(), p95_s=w.total_s.quantile(.95),
               ss_req_s=len(ss) / SS, ss_mean_s=ss.total_s.mean(), ss_p95_s=ss.total_s.quantile(.95),
               err_pct=100 * (~allw.ok).sum() / max(len(allw), 1),
               react_s=(mv.t.min() - t0) if len(mv) else np.nan, back_s=(bk.t.min() - t1) if len(bk) else np.nan)
    if ti is not None:
        win = ti[(ti.t >= t0) & (ti.t <= t1)]
        for t in ("edge", "fog", "cloud"): row[f"load_{t}"] = win[f"{t}_load"].mean()
    for s, p in pr.items():
        q = p[p.ok & (p.t >= t0) & (p.t <= t1)]
        row[f"sonde_{s}_ms"] = q.total_ms.mean()
    rows.append(row)

df = pd.DataFrame(rows)
print("== Par essai (s = secondes ; req_s = requêtes /process réussies par seconde)")
print(df.round(2).to_string(index=False))
cols = [c for c in df.columns if c not in ("tag", "mode")]
print("\n== Par mode : nombre d'essais, moyenne, écart-type entre essais")
print(df.groupby("mode")[cols].agg(["count", "mean", "std"]).round(2).T.to_string())
if {"sta", "dyn"} <= set(df["mode"]):
    s, d = df[df["mode"] == "sta"], df[df["mode"] == "dyn"]
    print()
    for c, lab in (("mean_s", "latence moyenne sur toute la charge"), ("ss_mean_s", "latence moyenne en régime établi"),
                   ("ss_p95_s", "latence p95 en régime établi")):
        print(f"{lab} : statique {s[c].mean():.2f} s -> dynamique {d[c].mean():.2f} s  (amélioration {100 * (1 - d[c].mean() / s[c].mean()):+.0f} %)")
    print(f"débit en régime établi : statique {s.ss_req_s.mean():.2f} -> dynamique {d.ss_req_s.mean():.2f} requêtes/s")

fig, ax = plt.subplots(2, 2, figsize=(15, 8), sharex="col")
for j, mode in enumerate(("sta", "dyn")):
    tags = [t for t, r in runs.items() if r["mode"] == mode]
    if not tags: continue
    r = runs[tags[0]]; t0, t1 = r["t0"], r["t1"]; ok = r["ld"][r["ld"].ok]
    a = ax[0][j]
    a.scatter(ok.t_fin - t0, ok.total_s, s=4, alpha=.35)
    a.plot(ok.t_fin - t0, ok.total_s.rolling(25, min_periods=5, center=True).median(), color="k", lw=1.6)
    a.axvspan(0, t1 - t0, alpha=.08)
    for _, e in r["ev"][r["ev"].service == "urllc"].iterrows(): a.axvline(e.t - t0, ls="--", color="r")
    a.set_title(f"{tags[0]} : temps de réponse de /process (urllc) vu depuis l'UE"); a.set_ylabel("secondes"); a.grid(alpha=.3)
    b = ax[1][j]
    if r["ti"] is not None:
        for t in ("edge", "fog", "cloud"): b.plot(r["ti"].t - t0, r["ti"][f"{t}_load"], label=t)
        b.axhline(0.7, ls=":", color="gray"); b.axvspan(0, t1 - t0, alpha=.08); b.legend()
    b.set_ylabel("charge CPU du tier"); b.set_xlabel("secondes depuis le début de la charge"); b.grid(alpha=.3)
plt.tight_layout(); plt.savefig(f"{R}/a11_timeline.png", dpi=130)

if {"sta", "dyn"} <= set(df["mode"]):
    g = df.groupby("mode")
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    for a, c, t in zip(ax, ("ss_mean_s", "ss_p95_s", "ss_req_s"), ("latence moyenne (s), régime établi", "latence p95 (s), régime établi", "débit (requêtes/s), régime établi")):
        mu, sd = g[c].mean(), g[c].std()
        a.bar(["statique", "dynamique"], [mu["sta"], mu["dyn"]], yerr=[sd["sta"], sd["dyn"]], capsize=5); a.set_title(t); a.grid(axis="y", alpha=.3)
    plt.tight_layout(); plt.savefig(f"{R}/a11_comparaison.png", dpi=130)
print("\nfigures :", f"{R}/a11_timeline.png", f"{R}/a11_comparaison.png")
