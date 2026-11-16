import os, pandas as pd
R = os.path.expanduser("~/6G/a-infra/a7-vm/results")
def stat(label, name, col, fname):
    f = os.path.join(R, fname)
    if os.path.exists(f):
        s = pd.read_csv(f)[col]
        print(f"{label:10s} {name:24s} n={len(s):2d}  moyenne={s.mean():8.3f}  écart-type={s.std():7.3f}  médiane={s.median():8.3f}")
for L in ("mono", "distribue"):
    stat(L, "enregistrement UE (s)", "registration_s", f"reg_{L}.csv")
    stat(L, "RTT UE->vm-k8s (ms)", "rtt_ms", f"rtt_{L}.csv")
    f = os.path.join(R, f"iperf_{L}.csv")
    if os.path.exists(f):
        for sens, g in pd.read_csv(f).groupby("sens"):
            s = g["mbps"]; print(f"{L:10s} débit {sens:4s} (Mbit/s)      n={len(s):2d}  moyenne={s.mean():8.2f}  écart-type={s.std():7.2f}")
