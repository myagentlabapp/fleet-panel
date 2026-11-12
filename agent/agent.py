#!/usr/bin/env python3
"""fleet-panel agent — 每台托管机运行, 定期自检上报 + 轮询取自愈指令执行。

用法:  python3 agent.py --server http://SERVER:8890 --host <本机名> [--interval 30]
自检项: load1 / mem% / disk% / docker容器数 / 到server延迟
自愈指令: server 下发 proc=service-restart|docker-restart, agent 收到后执行并回报。
"""
import argparse, json, os, re, subprocess, time, urllib.request, socket

def sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERR {e}"

def measure(token):
    # load
    try:
        l1 = float(open("/proc/loadavg").read().split()[0])
    except Exception:
        l1 = 0.0
    # mem
    out = sh("free -k | awk '/Mem/{print $2, $3}'")
    try:
        total, used = map(int, out.split())
        mem = used / total * 100.0
    except Exception:
        mem = 0.0
    # disk (根分区)
    out = sh("df -P / | tail -1 | awk '{print $5}' | tr -d '%'")
    try:
        disk = float(out)
    except Exception:
        disk = 0.0
    # docker 容器数
    dc = sh("docker ps -q 2>/dev/null | wc -l")
    docker = int(re.search(r"\d+", dc).group()) if re.search(r"\d+", dc) else 0
    latency = 0.0
    return {"host": args.host, "ip": local_ip(), "inet": "",
            "load1": round(l1, 2), "mem": round(mem, 1), "disk": round(disk, 1),
            "docker": docker, "latency": latency}

def local_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except Exception:
        return ""
    finally:
        if s: s.close()

def api(method, url, body=None, token=None, timeout=25):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json",
                                          "X-Fleet-Token": token or ""})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def run_cmd(proc, cmd):
    # 只放行白名单化的自愈动作, 不执行任意 shell
    if proc == "service-restart":
        # cmd like "rsyslog" -> systemctl restart rsyslog
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", cmd): return "bad name"
        return sh(f"sudo systemctl restart {cmd} && echo OK || echo FAIL")
    if proc == "docker-restart":
        # cmd like "container-name" -> docker restart container-name
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", cmd): return "bad name"
        return sh(f"docker restart {cmd} && echo OK || echo FAIL")
    return "unknown proc"

def main():
    global args
    ap = argparse.ArgumentParser(); ap.add_argument("--server", required=True)
    ap.add_argument("--host", required=True); ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--token", default=os.environ.get("FLEET_TOKEN", "dev-token"))
    args = ap.parse_args()
    base = args.server.rstrip("/")
    print(f"[agent] {args.host} -> {base}  every {args.interval}s")
    while True:
        m = measure()
        api("POST", base + "/api/agent/report", m, args.token)
        # 轮询自愈指令
        got = api("GET", base + f"/api/hosts/{args.host}/cmd", token=args.token)
        if got.get("ok") and got.get("cmd"):
            c = got["cmd"]
            print(f"[agent] self-heal {c['id']} {c['proc']} {c['cmd']}")
            out = run_cmd(c["proc"], c["cmd"])
            ok = "OK" in out
            api("POST", base + f"/api/hosts/{args.host}/result",
                {"id": c["id"], "ok": ok, "out": out[:400]}, args.token)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()