import numpy as np
import pandas as pd

CELLS = {"cell_1": 200.0, "cell_2": 500.0, "cell_3": 800.0}
P0, N_EXP, SHADOW = -30.0, 3.5, 4.0   # dBm à 1 m, exposant, écart-type shadowing (dB)
D_CORR = 20.0                          # distance de décorrélation du shadowing (m)
DT = 0.1
ROUTE = 1000.0                         # chaque UE parcourt la route une seule fois
INTERRUPTION_S = 0.05
HYST_DB, TTT_S = 3.0, 0.5

def run(strategy, speed, seed):
    rng = np.random.default_rng(seed)
    rho = np.exp(-speed * DT / D_CORR)             # corrélation temporelle (AR(1))
    shadow = {c: rng.normal(0, SHADOW) for c in CELLS}
    x, t, serving = 0.0, 0.0, "cell_1"
    prev_cell, last_ho_t = None, -99.0
    candidate, ttt_timer = None, 0.0
    n_ho = n_pp = 0
    t_subopt = 0.0
    while x < ROUTE:
        pw = {}
        for c, cx in CELLS.items():
            shadow[c] = rho * shadow[c] + np.sqrt(1 - rho**2) * rng.normal(0, SHADOW)
            pw[c] = P0 - 10 * N_EXP * np.log10(max(abs(x - cx), 1.0)) + shadow[c]
        best = max(pw, key=pw.get)
        if pw[best] - pw[serving] >= HYST_DB:
            t_subopt += DT                          # coût : cellule servante nettement moins bonne
        do_ho = False
        if strategy == "simple":
            do_ho = best != serving
        else:
            if best != serving and pw[best] - pw[serving] >= HYST_DB:
                if candidate != best:
                    candidate, ttt_timer = best, 0.0
                ttt_timer += DT
                do_ho = ttt_timer >= TTT_S
            else:
                candidate, ttt_timer = None, 0.0
        if do_ho:
            n_ho += 1
            if prev_cell == best and (t - last_ho_t) < 2.0:
                n_pp += 1
            prev_cell, serving, last_ho_t = serving, best, t
            candidate, ttt_timer = None, 0.0
        x += speed * DT
        t += DT
    interruption = n_ho * INTERRUPTION_S
    return dict(strategy=strategy, speed=speed, seed=seed, handovers=n_ho,
                pingpongs=n_pp, interruption_s=interruption,
                loss_pct=100 * interruption / t, subopt_s=round(t_subopt, 2))

rows = [run(s, v, seed) for s in ("simple", "hysteresis_ttt")
        for v in (5, 15, 30) for seed in range(10)]
df = pd.DataFrame(rows)
df.to_csv("data/processed/handover_results.csv", index=False)
print(df.groupby(["strategy", "speed"])[["handovers", "pingpongs", "interruption_s", "loss_pct", "subopt_s"]]
        .agg(["mean", "std"]).round(2))
