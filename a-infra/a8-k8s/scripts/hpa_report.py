import os, sys, pandas as pd
E = sys.argv[1]; R = os.path.expanduser("~/6G/a-infra/a8-k8s/results")
h = pd.read_csv(f"{R}/hpa_{E}.csv"); p = pd.read_csv(f"{R}/probe_hpa_{E}.csv", dtype={"code": str})
m = dict(l.strip().split("=") for l in open(f"{R}/meta_{E}.txt")); t0, t1 = float(m["load_start"]), float(m["load_end"])
h["rep"] = pd.to_numeric(h.replicas, errors="coerce")
base = h[h.t < t0].rep.max()
during = h[(h.t >= t0) & (h.t <= t1)]
peak = during.rep.max()
t_up = during[during.rep > base].t.min() - t0
t_peak = during[during.rep >= peak].t.min() - t0
t_down = h[(h.t >= t1) & (h.rep <= base)].t.min() - t1
print(f"réplicas : départ={base:.0f} pic={peak:.0f} | 1re montée {t_up:.0f} s après le début de la charge | pic atteint après {t_peak:.0f} s | retour à {base:.0f} : {t_down:.0f} s après la fin")
print(f"CPU maximal vu par le HPA : {pd.to_numeric(h.cpu_percent, errors='coerce').max():.0f} % de la demande (cible 50 %)")
ok = p[p.code == "200"]
def s(x): return f"n={len(x):4d}  moyenne={x.total_ms.mean():7.0f} ms  médiane={x.total_ms.median():7.0f}  p95={x.total_ms.quantile(.95):7.0f}"
print("latence sans charge       :", s(ok[ok.t < t0]))
print("latence AVANT autoscaling :", s(ok[(ok.t >= t0) & (ok.t < t0 + t_up)]))
print("latence APRÈS autoscaling :", s(ok[(ok.t >= t0 + t_peak + 20) & (ok.t <= t1)]))
