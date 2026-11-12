"""Carve the embedded frontend bundle out of the 1Panel core binary.

The Go binary embeds ``assets/js/*.js`` and ``assets/css/*.css`` with
``go:embed``; files are stored gzip-compressed back to back.  This tool scans for
gzip members and writes the ones that decode to JS/CSS text.
"""
import gzip
import os
import re
import sys
import zlib

SRC = sys.argv[1]
DST = sys.argv[2]
os.makedirs(DST, exist_ok=True)

data = open(SRC, "rb").read()
start = data.find(b"assets/js/")
end = data.find(b"assets/css/")
region_start = max(0, start - 1024)
region = data[: data.find(b"assets/img") + 1 if b"assets/img" in data else len(data)]
print("binary", len(data), "js-list@", start, "css-list@", end)

i = 0
n = 0
while i < len(region):
    i = region.find(b"\x1f\x8b\x08", i)
    if i < 0:
        break
    try:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        out = d.decompress(region[i:])
        if not d.eof:
            raise ValueError("truncated")
        consumed = len(region[i:]) - len(d.unused_data)
        if len(out) > 400:
            head = out[:300].decode("utf-8", "replace")
            if "�" not in head[:50]:
                n += 1
                ext = ".css" if (".md-editor" in head or "@layer" in head or "{--" in head) else ".js"
                with open(os.path.join(DST, f"carve_{n:03d}{ext}"), "wb") as f:
                    f.write(out)
        i += max(consumed, 3)
    except Exception:
        i += 3
print("carved", n)
