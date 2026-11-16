import os, socket, time, hashlib
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify(pod=socket.gethostname(), node=os.getenv("NODE_NAME", "?"),
                   tier=os.getenv("TIER", "?"))

@app.route("/process")
def process():                      # charge CPU simulant un traitement (ex. inférence)
    n = int(request.args.get("n", 200000)); t = time.time(); h = b"x"
    for _ in range(n): h = hashlib.sha256(h).digest()
    return jsonify(node=os.getenv("NODE_NAME", "?"), proc_ms=round((time.time()-t)*1000, 2))
