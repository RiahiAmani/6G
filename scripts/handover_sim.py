import numpy as np
import pandas as pd

CELLS = {"cell_1": 200.0, "cell_2": 500.0, "cell_3": 800.0}
P0, N_EXP, SHADOW = -30.0, 3.5, 4.0      # dBm à 1 m, exposant, écart-type shadowing (dB)
DT, DURATION = 0.1, 60.0                  # pas 0,1 s, 60 s de simulation
INTERRUPTION_S = 0.05                     # coupure par handover : 50 ms
HYST_DB, TTT_S = 3.0, 0.5                 # stratégie 2

def rx_power(x, cell_x, rng):
    d = max(abs(x - cell_x), 1.0)
    return P0 - 10 * N_EXP * np.log10(d) + rng.normal(0, SHADOW)

def run(strategy, speed, seed):
    rng = np.random.default_rng(seed)
    x, serving, history = 0.0, "cell_1", []
    ttt_timer, candidate = 0.0, None
    n_ho, n_pingpong, last_ho_t = 0, 0, -99.0
    prev_cell = None
    for step in range(int(DURATION / DT)):
        t = step * DT
        x = (x + speed * DT) % 1000
        pw = {c: rx_power(x, cx, rng) for c, cx in CELLS.items()}
        best = max(pw, key=pw.get)
        do_ho = False
        if strategy == "simple":
            do_ho = best != serving
            target = best
        else:
            target = best
            if best != serving and pw[best] - pw[serving] >= HYST_DB:
                if candidate != best:
                    candidate, ttt_timer = best, 0.0
                ttt_timer += DT
                if ttt_timer >= TTT_S:
                    do_ho = True
            else:
                candidate, ttt_timer = None, 0.0
        if do_ho:
            n_ho += 1
            if prev_cell == target and (t - last_ho_t) < 2.0:
                n_pingpong += 1
            prev_cell, serving, last_ho_t = serving, target, t
            candidate, ttt_timer = None, 0.0
        history.append(t)
    interruption = n_ho * INTERRUPTION_S
    return dict(strategy=strategy, speed=speed, seed=seed, handovers=n_ho,
                pingpongs=n_pingpong, interruption_s=interruption,
                loss_pct=100 * interruption / DURATION)

rows = []
for strategy in ("simple", "hysteresis_ttt"):
    for speed in (5, 15, 30):               # piéton/vélo, voiture lente, voiture
        for seed in range(10):              # 10 répétitions (minimum exigé : 3)
            rows.append(run(strategy, speed, seed))

df = pd.DataFrame(rows)
df.to_csv("data/processed/handover_results.csv", index=False)
summary = df.groupby(["strategy", "speed"])[["handovers", "pingpongs", "interruption_s", "loss_pct"]] \
            .agg(["mean", "std"]).round(2)
print(summary)

