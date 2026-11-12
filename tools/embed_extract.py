"""List and extract go:embed gzip members from the 1Panel core binary."""
import gzip
import io
import json
import os
import sys
import zlib

SRC, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(SRC, "rb").read()
members = []
i = 0
while True:
    i = data.find(b"\x1f\x8b\x08\x00\x00\x00\x00\x00", i)
    if i < 0:
        break
    try:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        out = d.decompress(data[i:i + 80 * 1024 * 1024])
        if d.eof:
            members.append((i, len(out), out[:200]))
            i += 16
            continue
    except Exception:
        pass
    i += 2
print("members", len(members), file=sys.stderr)
if MODE == "list":
    for off, n, head in members:
        print(off, n, head[:80])
else:
    os.makedirs(OUT, exist_ok=True)
    json.dump([[o, n, h.decode("utf-8", "replace")] for o, n, h in members],
              open(os.path.join(OUT, "_index.json"), "w"), ensure_ascii=False, indent=0)
    for k, (off, n, head) in enumerate(members):
        try:
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            out = d.decompress(data[off:off + 80 * 1024 * 1024])
        except Exception:
            continue
        with open(os.path.join(OUT, "m_%04d" % k), "wb") as f:
            f.write(out)
