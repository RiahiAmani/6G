import hashlib, sys, time
# mode « UE seul » : même traitement, exécuté localement sur la VM de l'UE
# usage : python3 measure_local.py <runs> <n> [série]
runs, n = int(sys.argv[1]), int(sys.argv[2]); serie = sys.argv[3] if len(sys.argv) > 3 else "1"
for _ in range(runs):
    t = time.time(); h = b"x"
    for _ in range(n): h = hashlib.sha256(h).digest()
    ms = (time.time() - t) * 1000
    print(f"{serie},ue,{n},0,{ms/1000:.4f},{ms:.2f}")
