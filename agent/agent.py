#!/usr/bin/env python3
"""fleet-panel agent — 每台托管机运行, 定期自检上报 + 轮询取自愈指令执行。

用法:  python3 agent.py --server http://SERVER:8890 --host <本机名> [--interval 30]
自检项: load1 / mem% / disk% / docker容器数 / 到server延迟
自愈指令: server 下发 proc=service-restart|docker-restart, agent 收到后执行并回报。
"""
import argparse, json, os, re, subprocess, threading, time, urllib.request, socket

def sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"ERR {e}"

def ping_ms(addr=None, timeout=2, count=3):
    if addr is None:
        addr = os.environ.get("FLEET_HUB", "")
    if not addr:
        return 0.0
    """ICMP 往返延迟(ms)。面板 hub 即面板所在地, 与面板对节点的探测对称。
    发 3 包取最小值, 抗链路抖动/丢包。"""
    try:
        o = sh(f"ping -n -c {count} -i 0.3 -W {timeout} {addr}")
        hits = [float(x) for x in re.findall(r"time=([\d.]+)", o)]
        return round(min(hits), 1) if hits else 0.0
    except Exception:
        return 0.0

def _facts():
    """节点实况: 系统服务 / docker / nginx / 证书 / cron。
    面板的多机管理卡片直接读这份上报, 不再从面板侧 SSH 现取。
    缺二进制的机器(没 docker / 没 nginx)不会崩, 只是 ok=False。"""
    f = {}
    # --- systemd 运行中的服务 ---
    o = sh("systemctl list-units --type=service --state=running --plain --no-legend --no-pager 2>/dev/null")
    names = []
    for ln in o.splitlines():
        p = ln.split()
        if p and p[0].endswith(".service"):
            names.append(p[0][:-8])
    f["services"] = {"count": len(names), "names": names[:40]}

    # --- docker: 先判存在, 再取容器 ---
    if sh("command -v docker 2>/dev/null"):
        o = sh('docker ps --format "{{.Names}}|{{.State}}" 2>/dev/null')
        items = []
        for ln in o.splitlines():
            if "|" in ln:
                nm, st = ln.split("|", 1)
                items.append({"name": nm, "state": st})
        f["docker"] = {"ok": True, "count": len(items), "items": items[:20]}
    else:
        f["docker"] = {"ok": False, "count": 0, "items": []}

    # --- nginx: 站点数 ---
    has_nginx = bool(sh("command -v nginx 2>/dev/null"))
    o = sh("ls -1 /etc/nginx/sites-enabled/ /etc/nginx/conf.d/*.conf 2>/dev/null")
    sites = len([x for x in o.splitlines() if x.strip()])
    f["nginx"] = {"ok": has_nginx, "sites": sites}

    # --- 证书: 数量 + 最早到期 ---
    files = sh("for d in /etc/nginx/ssl /etc/letsencrypt/live /root/.acme.sh; do "
               "find \"$d\" -maxdepth 3 \\( -name '*.pem' -o -name '*.crt' \\) 2>/dev/null; "
               "done | sort -u | head -50")
    flist = [x for x in files.splitlines() if x.strip()]
    if flist:
        o = sh("for f in " + " ".join("'" + x.replace("'", "") + "'" for x in flist[:50]) + "; do "
               "openssl x509 -in \"$f\" -noout -enddate 2>/dev/null | cut -d= -f2-; done")
        ends = sorted(x.strip() for x in o.splitlines() if x.strip() and "=" not in x)
        f["certs"] = {"count": len(flist), "earliest": (ends[0] if ends else "")}
    else:
        f["certs"] = {"count": 0, "earliest": ""}

    # --- cron ---
    o = sh("crontab -l 2>/dev/null")
    cl = [x for x in o.splitlines() if x.strip() and not x.lstrip().startswith("#")]
    f["cron"] = {"count": len(cl), "items": [x.strip()[:120] for x in cl[:10]]}
    return f


def measure():
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
    try:
        facts = _facts()
    except Exception:
        facts = {}
    # 自愈: 用本轮已采到的 disk/mem 判定, 省一次 df/free
    try:
        facts["heal"] = _selfheal(disk, mem)
    except Exception as e:
        facts["heal"] = {"actions": [], "blocked": [], "notes": [],
                         "error": str(e)[:200]}
    return {"host": args.host, "ip": local_ip(), "inet": "",
            "load1": round(l1, 2), "mem": round(mem, 1), "disk": round(disk, 1),
            "docker": docker, "latency": ping_ms(), "facts": facts}

def local_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except Exception:
        return ""
    finally:
        if s: s.close()


# ---------- 自愈 ----------
# 只修三类, 全是本地动作, 不依赖网络/面板/SSH:
#   1) 关键服务挂了   -> systemctl restart
#   2) 磁盘 > 90%     -> journal vacuum + 清 /tmp 顶层老文件
#   3) 内存 > 95%     -> 只记录, 不动手(杀进程风险不可控)
# wg0/wg-quick/wg-easy 一律不碰 —— 隧道归别处管。
HEAL_SERVICES = ("sshd", "docker", "fail2ban", "cron")
HEAL_DISK_PCT = 90
HEAL_MEM_PCT = 95
HEAL_COOLDOWN = 300      # 同一 target 两次修复最小间隔(秒)
HEAL_MAX_FAIL = 5        # 同一 target 连续失败上限, 到顶就停手
_HEAL_STATE = {"last": {}, "fails": {}, "blocked": set(),
               "actions": [], "notes": []}   # 进程内存态, agent 重启后清零


def _rc(cmd, timeout=20):
    """执行并返回退出码(不看输出内容 —— 用 sh() 的输出判成功会被空输出骗到)。"""
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL).returncode
    except Exception:
        return -1


def _heal_svc_ok(name):
    """服务该不该管: 单元存在 且 已 enable。人工 disable 掉的不自动拉起, 避免和运维操作打架。"""
    if _rc(f"systemctl cat {name} >/dev/null 2>&1") != 0:
        return False
    return sh(f"systemctl is-enabled {name} 2>/dev/null").strip() == "enabled"


def _heal_action(target, action, fn):
    """执行一次修复, 带冷却 + 失败上限。fn 返回 (ok, err)。"""
    now = int(time.time())
    st = _HEAL_STATE
    if target in st["blocked"]:
        return None
    last = st["last"].get(target, 0)
    if now - last < HEAL_COOLDOWN:
        return None
    st["last"][target] = now
    try:
        ok, err = fn()
    except Exception as e:
        ok, err = False, str(e)
    if ok:
        st["fails"][target] = 0
    else:
        st["fails"][target] = st["fails"].get(target, 0) + 1
        if st["fails"][target] >= HEAL_MAX_FAIL:
            st["blocked"].add(target)
    st["actions"].append({"at": now, "target": target, "action": action,
                          "ok": bool(ok), "err": str(err or "")[:200]})
    del st["actions"][:-20]
    return ok


def _selfheal(disk_pct=None, mem_pct=None):
    """每轮上报前自检自修。全部本地执行, 网络/面板/SSH 断了照样工作。"""
    st = _HEAL_STATE

    # --- 1) 关键服务 ---
    for svc in HEAL_SERVICES:
        if not _heal_svc_ok(svc):
            continue          # 不存在或被人为 disable, 不管
        if sh(f"systemctl is-active {svc} 2>/dev/null").strip() == "active":
            continue

        def _do_svc(s=svc):
            sh(f"systemctl restart {s} 2>&1", timeout=60)
            ok = sh(f"systemctl is-active {s} 2>/dev/null").strip() == "active"
            return ok, "" if ok else "restart 后仍未 active"

        _heal_action(svc, f"systemctl restart {svc}", _do_svc)

    # --- 2) 磁盘 ---
    try:
        d = float(disk_pct if disk_pct is not None else
                  (sh("df -P / | awk 'NR==2{gsub(\"%\",\"\",$5); print $5}'").strip() or 0))
    except Exception:
        d = 0.0
    if d > HEAL_DISK_PCT:
        def _do_disk():
            sh("journalctl --vacuum-size=500M 2>&1", timeout=60)
            sh("find /tmp -maxdepth 1 -type f -mtime +7 -delete 2>/dev/null", timeout=30)
            after = sh("df -P / | awk 'NR==2{gsub(\"%\",\"\",$5); print $5}'").strip()
            try:
                freed = float(after) <= d
            except Exception:
                freed = True
            return freed, "" if freed else f"清理后仍 {after}%"
        _heal_action("disk", "journal vacuum + 清 /tmp 老文件", _do_disk)

    # --- 3) 内存: 只记录 ---
    try:
        m = float(mem_pct if mem_pct is not None else 0)
    except Exception:
        m = 0.0
    if m > HEAL_MEM_PCT:
        st["notes"].append({"at": int(time.time()),
                            "msg": f"mem {m:.1f}% 超过 {HEAL_MEM_PCT}%, 未处理(杀进程风险不可控)"})
        del st["notes"][:-10]

    return {"actions": list(st["actions"]), "blocked": sorted(st["blocked"]),
            "notes": list(st["notes"])}

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


# 可下发的 AI CLI 白名单 —— 与面板 api_cmd 的前缀校验保持一致(双保险)
AI_CLIS = ("claude", "codex", "opencode", "gemini", "qwen", "aider")


def _cli_segment(cmd):
    """命令形如 `mkdir -p ~/ws && cd ~/ws && claude -p '...'`; 只要 && 链里有一段是以
    白名单 CLI 开头的就放行。返回该 CLI 名, 没有则返回空串。这个校验限制的是"能不能从这个
    通道执行任意 shell", 不是限制 mkdir/cd 之类的准备动作。"""
    for seg in str(cmd or "").split("&&"):
        seg = seg.strip()
        if not seg:
            continue
        head = os.path.basename(seg.split()[0])
        if head in AI_CLIS:
            return head
    return ""


def run_ai_task(cmd, timeout=180):
    """在节点本地执行面板下发的 AI 诊断命令, 返回 (ok, out)。
    任务由面板拼好(CLI 路径/模板/参数/workdir), agent 只负责跑 —— 面板不再 SSH 进来,
    所以链路抖动不会打断正在跑的诊断。"""
    cmd = (cmd or "").strip()
    if not cmd:
        return False, "empty cmd"
    if not _cli_segment(cmd):
        return False, f"refused: no segment starts with one of {AI_CLIS}"
    try:
        r = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True,
                           timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[-20000:]
    except subprocess.TimeoutExpired as e:
        part = (e.stdout or b"") + (e.stderr or b"")
        if isinstance(part, bytes):
            part = part.decode(errors="replace")
        return False, (f"TIMEOUT after {timeout}s\n" + str(part)[-6000:]).strip()
    except Exception as e:
        return False, f"ERR {e}"


def _ai_worker(task_id, cmd, timeout):
    """后台线程跑 AI 任务并回传 —— 诊断常要几十秒到几分钟, 不能卡住 30s 上报/轮询循环。"""
    ok, out = run_ai_task(cmd, timeout)
    print(f"[agent] ai-report {task_id} {'ok' if ok else 'fail'} ({len(out)} bytes)")
    api("POST", base + f"/api/hosts/{args.host}/result",
        {"id": task_id, "ok": ok, "out": out[:20000]}, args.token)

def main():
    global args, base
    ap = argparse.ArgumentParser(); ap.add_argument("--server", required=True)
    ap.add_argument("--host", required=True); ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--token", default=os.environ.get("FLEET_TOKEN", "dev-token"))
    args = ap.parse_args()
    base = args.server.rstrip("/")
    print(f"[agent] {args.host} -> {base}  every {args.interval}s")
    running = set()          # 正在跑的 ai-report 任务 id, 避免同一任务重复执行
    while True:
        m = measure()
        api("POST", base + "/api/agent/report", m, args.token)
        # 轮询自愈指令
        got = api("GET", base + f"/api/hosts/{args.host}/cmd", token=args.token)
        if got.get("ok") and got.get("cmd"):
            c = got["cmd"]
            if c["proc"] == "ai-report":
                # 长任务: 丢给后台线程, 主循环继续上报
                if c["id"] not in running:
                    running.add(c["id"])
                    to = int(c.get("timeout") or 180)
                    print(f"[agent] ai-report {c['id']} start (timeout {to}s)")

                    def _wrap(tid, cmd, to):
                        try:
                            _ai_worker(tid, cmd, to)
                        finally:
                            running.discard(tid)
                    threading.Thread(target=_wrap, args=(c["id"], c["cmd"], to), daemon=True).start()
            else:
                print(f"[agent] self-heal {c['id']} {c['proc']} {c['cmd']}")
                out = run_cmd(c["proc"], c["cmd"])
                ok = "OK" in out
                api("POST", base + f"/api/hosts/{args.host}/result",
                    {"id": c["id"], "ok": ok, "out": out[:400]}, args.token)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()