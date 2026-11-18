import os, pandas as pd
R = os.path.expanduser("~/6G/a-infra/a9-docker/results")
def show(f, keys, cols):
    p = os.path.join(R, f)
    if os.path.exists(p):
        d = pd.read_csv(p); print(f"\n== {f}")
        print(d.groupby(keys)[cols].agg(["count", "mean", "std"]).round(2))
show("iperf_tcp.csv", ["via", "sens"], ["mbps", "retrans"])
show("iperf_udp.csv", ["rate_mbps"], ["mbps", "jitter_ms", "lost_pct"])
show("iperf_parallel.csv", ["streams"], ["mbps"])
