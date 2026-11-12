"""Run the 1Panel core binary locally and snapshot its embedded web assets.

The frontend bundle lives inside 1panel-core behind go:embed.  Starting the
binary under strace records every path it tries to open, which hands us the
exact list of embedded ``assets/...`` names; the files themselves are dumped
with gdb through ``runtime.etext_addr``-free ``openat`` interception instead:
we simply start 1Panel, fetch the assets from its own port, and stop it.
"""
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request

BIN = sys.argv[1]
OUT = sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 19999
DATA = "/tmp/1p1data"


def free(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


if not free(PORT):
    sys.exit("port busy: %d" % PORT)

shutil.rmtree(DATA, ignore_errors=True)
os.makedirs(DATA, exist_ok=True)
env = dict(os.environ, _1PANEL_DATA_DIR=DATA, PANEL_BASE_DIR=DATA)
p = subprocess.Popen([BIN, "-mode", "dev", "-port", str(PORT), "-ssl", "disable",
                      "-base-dir", DATA, "-data-dir", DATA],
                     stdout=open("/tmp/1p1.log", "wb"), stderr=subprocess.STDOUT,
                     env=env)
try:
    for _ in range(120):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % PORT, timeout=1).read(64)
            break
        except Exception:
            time.sleep(0.5)
    else:
        print("1Panel did not come up; see /tmp/1p1.log")
finally:
    p.send_signal(signal.SIGTERM)
    time.sleep(1)
    p.kill()
print("done")
