"""Download every asset referenced by the 1Panel panel that is proxied through 192.168.1.120:28999.

The upstream panel refuses non-browser clients, so the download is performed by a
same-origin fetch() loop inside the already-authenticated browser page and the
base64 payloads are handed back to this script through a temp file.
"""
import base64
import json
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/yy/fleet-panel/ref/frontend"
BATCH = sys.argv[2] if len(sys.argv) > 2 else "/tmp/1pui/batch.json"

os.makedirs(OUT, exist_ok=True)
data = json.load(open(BATCH))
n = 0
for path, b64 in data.items():
    if b64 is None:
        continue
    dst = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(base64.b64decode(b64))
    n += 1
print("wrote", n, "files to", OUT)
