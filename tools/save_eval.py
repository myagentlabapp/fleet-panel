"""Save base64 payloads from a conhub browser_eval result file to disk."""
import base64
import json
import os
import sys

src, dst = sys.argv[1], sys.argv[2]
raw = json.load(open(src))
res = raw.get("result", raw)
if isinstance(res, str):
    res = json.loads(res)
if isinstance(res, dict) and isinstance(res.get("result"), str):
    res = json.loads(res["result"])
n = 0
for path, b64 in res.items():
    if not isinstance(b64, str) or not b64.startswith("data:"):
        continue
    out = os.path.join(dst, path.lstrip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64.split(",", 1)[1]))
    n += 1
    print("wrote", out, os.path.getsize(out))
print("total", n)
