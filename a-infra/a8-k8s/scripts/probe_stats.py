import sys, pandas as pd
d = pd.read_csv(sys.argv[1], dtype={"code": str})
ok = d[d.code == "200"]; ko = d[d.code != "200"]
gap = ok.t.diff().max() if len(ok) > 1 else float("nan")
print(f"requêtes={len(d)}  échecs={len(ko)} ({100*len(ko)/len(d):.1f} %)  coupure max={gap:.2f} s")
if len(ok):
    print(f"latence (succès) : moyenne={ok.total_ms.mean():.1f} ms  médiane={ok.total_ms.median():.1f}  p95={ok.total_ms.quantile(.95):.1f}  max={ok.total_ms.max():.1f}")
