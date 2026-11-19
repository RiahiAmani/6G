import csv, json, os, shlex, subprocess, time
os.environ["LC_ALL"] = "C"
RUN  = os.environ.get("RUN", "test")
MODE = os.environ.get("MODE", "dynamic")     # dynamic : décide et déplace ; observe : mesure seulement (référence statique)
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(D, "results"); os.makedirs(R, exist_ok=True)

LAT = {"edge": 2, "fog": 10, "cloud": 40}            # latence ajoutée par netem (ms)
CAP = {"edge": 1000, "fog": 2000, "cloud": 3000}     # millicores (docker update --cpus)
SERVICES = {                                         # service : (latence max ms, préférence, nodePort)
    "urllc": (15, "near", 30101),
    "embb":  (30, "far",  30102),
    "mmtc":  (200, "far", 30103),
}
THRESH, MIN_STAY, PERIOD = 0.7, 60, 10               # seuil de charge, durée mini entre deux déplacements (s), période (s)
last_move = {}

def sh(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()

def milli(v): return int(v[:-1]) if v.endswith("m") else int(float(v) * 1000)

def used(selector):                                  # CPU consommé (millicores) par les pods choisis ; None si indisponible
    rc, out = sh("kubectl top pods -l %s --no-headers" % selector)
    if rc != 0: return None
    return sum(milli(l.split()[1]) for l in out.splitlines() if l.strip())

def current(svc):
    return sh("kubectl get deploy %s -o jsonpath='{.spec.template.spec.nodeSelector.tier}'" % svc)[1]

def decide(svc, cur, max_lat, pref, loads, own):
    ok = [t for t in ("edge", "fog", "cloud") if LAT[t] <= max_lat]
    if pref == "far": ok.reverse()
    for t in ok:
        projected = loads[t] + (0 if t == cur else own[svc] / CAP[t])
        if projected < THRESH: return t
    return cur                                        # tout est saturé : on ne bouge pas

def move(svc, target):
    patch = {"spec": {"template": {"metadata": {"labels": {"tier": target}},
             "spec": {"nodeSelector": {"tier": target},
                      "containers": [{"name": "app", "env": [{"name": "TIER", "value": target}]}]}}}}
    sh("kubectl patch deploy %s -p %s" % (svc, shlex.quote(json.dumps(patch))))

def opener(name, header):
    path = os.path.join(R, "%s_%s.csv" % (name, RUN)); new = not os.path.exists(path)
    f = open(path, "a", newline=""); w = csv.writer(f)
    if new: w.writerow(header); f.flush()
    return f, w

flog, wlog = opener("log", ["timestamp", "tier", "service", "cpu_m", "latency_ms", "replicas"])   # format commun pour B, C, D
fev, wev = opener("events", ["timestamp", "service", "from_tier", "to_tier", "edge_load", "fog_load", "cloud_load", "own_cpu_m"])
fti, wti = opener("tiers", ["timestamp", "edge_load", "fog_load", "cloud_load"])

print("placer RUN=%s MODE=%s (Ctrl+C pour arrêter)" % (RUN, MODE), flush=True)
while True:
    start = time.time()
    raw = {t: used("tier=%s" % t) for t in LAT}
    own = {s: used("app=%s" % s) for s in SERVICES}
    if None in raw.values() or None in own.values():
        print("%s métriques indisponibles, on attend" % time.strftime("%X"), flush=True)
        time.sleep(PERIOD); continue
    loads = {t: raw[t] / CAP[t] for t in LAT}
    now = int(time.time())
    wti.writerow([now] + ["%.3f" % loads[t] for t in ("edge", "fog", "cloud")])
    line = "%s edge=%.2f fog=%.2f cloud=%.2f |" % (time.strftime("%X"), loads["edge"], loads["fog"], loads["cloud"])
    for svc, (lat, pref, port) in SERVICES.items():
        cur = current(svc)
        if not cur: continue
        target = decide(svc, cur, lat, pref, loads, own) if MODE == "dynamic" else cur
        if target != cur and time.time() - last_move.get(svc, 0) > MIN_STAY:
            move(svc, target); last_move[svc] = time.time()
            wev.writerow([now, svc, cur, target] + ["%.3f" % loads[t] for t in ("edge", "fog", "cloud")] + [own[svc]])
            print("%s >>> DÉPLACEMENT %s : %s -> %s (service %d m)" % (time.strftime("%X"), svc, cur, target, own[svc]), flush=True)
            cur = target
        t = sh("curl -s -o /dev/null -m 2 -w '%%{time_total}' http://127.0.0.1:%d/" % port)[1]
        lat_ms = round(float(t.replace(",", ".")) * 1000, 1) if t else ""
        rep = sh("kubectl get deploy %s -o jsonpath='{.status.readyReplicas}'" % svc)[1] or 0
        wlog.writerow([now, cur, svc, own[svc], lat_ms, rep])
        line += " %s@%s %dm" % (svc, cur, own[svc])
    for f in (flog, fev, fti): f.flush()
    print(line, flush=True)
    time.sleep(max(1, PERIOD - (time.time() - start)))
