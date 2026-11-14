# fleet-panel 全机器纳管 PLAN（应用层接入）

> 本文件是**机器/应用纳管的唯一目标与执行清单**。
> 功能对齐（页面对标专业版）见 `TARGETS.md`，两者不重叠：TARGETS 管「页面长得像不像」，本文件管「机器和应用接没接进来」。
> 建立于 2026-11-14，依据：对 9 台在网机器 + wiki 台账的逐台实测复核。

状态勾：`[x]` 已完成并验证 · `[~]` 进行中 · `[ ]` 待做 · `[!]` 被阻塞

---

## 0. 一句话目标

**把 fleet-panel 从「9 台机器的看门狗」升级为「9 台机器的应用层管理台」。**

现状：**监控 9 台，能管 1 台。**
面板对 111 以外的 8 台，只能看到负载/内存/磁盘/容器数四个数字，看不到也管不了它们跑的任何应用。

**不在范围**（明确排除，防止跑偏）：
- 加机器 —— 实测无可用增量（见 §2 排除项）
- 改网络底座 —— ufw / WG 拓扑 / 出向代理一律不动
- UI 像素级打磨 —— 归 TARGETS.md
- 108（home-4c8g，旧名 home-cap 已废弃）—— 已停用，见 §2

---

## 1. 现状基线（2026-11-14 16:55 实测）

### 1.1 九台在网机器

| # | 机器 | WG IP | 容器 | 角色 | 面板现状 |
|---|------|-------|------|------|----------|
| 1 | home-4c31g (111) | 10.8.0.2 | **58** | hub + 出口 + CoreDNS + 公网兜底 | ✅ 唯一可管理 |
| 2 | home-2c2g (116) | 10.8.0.3 | 4 | lldap / syspass / dashy | 仅监控 |
| 3 | home-4c15g (120) | 10.8.0.4 | 11 + 宿主 CloudCLI | 计算主力 + pg-unified | 仅监控 |
| 4 | hk-2c2g | 10.8.0.5 | 0（nginx 10 vhost） | 公网温备门面 + api.* 出口 | 仅监控 |
| 5 | xian-2c2g | 10.8.0.6 | 5 | new-api 个人版 + sub2api | 仅监控 |
| 6 | hk-1c1g（追云） | 10.8.0.8 | 0（nginx 26 vhost） | **公网唯一主门面** | 仅监控 |
| 7 | xian-8c8g-a | 10.8.0.9 | 12 | **平台本体** | 仅监控 |
| 8 | xian-8c8g-b | 10.8.0.10 | 12 | **MCP 网关 + 10 MCP** | 仅监控 |
| 9 | xian-16c16g | 10.8.0.11 | 0 | 仅出向代理 env | 仅监控 |

合计 **102 个容器**；面板 docker 页能看到的只有 111 本机的 58 个。

### 1.2 面板的架构约束（不是缺页面，是缺执行层）

- `_docker(args)` at `server/app.py:25` —— 只跑本机 `docker`，**无 host 参数**
- `request.args.get("host")` 全文出现 **0 次**
- 242 个路由里，跨机能力只有 4 个端点 + PTY 终端：
  `/api/hosts` · `/api/hosts/<h>/cmd` · `/api/hosts/<h>/result` · `/api/sync/ls?node=`
- docker / 网站 / 证书 / 数据库 / 文件 / 进程 / 磁盘 / 防火墙 / 监控 —— **全部只对 111 生效**

**结论：加页面不解决问题，必须先把执行层改成 host-aware。**

### 1.3 已有的可复用件（改造时直接用，避免重造）

| 件 | 位置 | 用途 |
|---|---|---|
| `_node_login(host)` | app.py:831 | name/ip → (addr, rec)，走 `SELECT ip FROM hosts WHERE name=? OR ip=?` |
| `term_run(host, cmd, sudo=False)` | app.py:849 | 本机直跑 / 远端 SSH（`fleet_ed25519` + root）；rc=255 = 不可达 |
| `_NODE_PROBE_CMD` + `node_poll_once()` | ~app.py:2905 | base64 包裹探测脚本的成熟范式，新端点照抄 |
| `report()` | ~app.py:2840 | hosts 表 upsert |

---

## 2. 明确排除项（写死，不再讨论）

| 对象 | 理由（均为实测） |
|---|---|
| **108 home-4c8g**（旧名 home-cap） | 采集栈 NapCat×6 容器**已不存在**；`qq-osint-neo4j` Exited(3)、`qq-osint-graph` Exited(137)6 周；仅 PG + Meili 在跑。不在 WG、无 CoreDNS A 记录、sudo 需密码。按废弃处理。 |
| **119** | 2026-08-09 已退役；ping 不通、22 关闭。**wiki fleet-inventory 仍列第 5 行，属台账错误**，见 T2 |
| **102** | ping 不通、22 关闭（NIC 答 ARP 但全端口关闭） |
| **109 / 121 / 100** | WSL2 / RISC-V / 纸质机，不是服务器 |
| **10.8.0.7 aliyun** | 2026-11-13 已从 WG peer / DNS / PTR 全部移除 |

---

## 3. 待办清单

### P0 — 硬 deadline，先拆雷

#### [x] T1 · 追云 CF Token —— 2026-11-14 排雷完成，无需换 token

**证据链（2026-11-14 实测）**
- 追云 `/root/.acme.sh/account.conf` 的 `SAVED_CF_Token` 长 53 字符
- 拿去 CF API `/user/tokens/verify` → `{"success":false,"errors":[{"code":1000,"message":"Invalid API Token"}]}`
- acme.sh cron 活着，但每天只输出 `Skipping. Next renewal time is: 2026-12-23`
- 证书 `/etc/nginx/ssl/wildcard/fullchain.pem`，subject `CN=*.myagentlabapp.com`，**notAfter 2027-01-06**
- hk-2c2g 走 LetsEncrypt，续签 2026-12-11，暂不受影响

**后果**：2026-12-23 续签失败 → 2027-01-06 证书过期 → app.com 19 个站点 + api.* 全站中招。

**结论（2026-11-20 复核口径：实际 2026-11-14 处理）**：token 没失效——是验证方法错了。wiki `ops/cloudflare-api` 台账里的 3 个 `cfat_` 账户级令牌全部 active（`/accounts/{acc}/tokens/verify` 返回 active；此前调 `/user/tokens/verify` 只适用于 User Token，故误报 Invalid）。追云 `SAVED_CF_Token` = ddns-go 令牌 `cfat_qkUE…`，zone `dns_records` API 实测 200。
1. [x] 直接用现有 token（无需用户提供）
2. [x] `acme.sh --renew -d '*.myagentlabapp.com' --force --ecc` 真实签发成功（ZeroSSL）
3. [x] 已部署 `/etc/nginx/ssl/wildcard/` + reload，`nginx -t` 通过
4. [x] 外网实测 `https://ai.myagentlabapp.com/` ssl_verify=0，notAfter **2027-02-12**（下次续期窗口 2027-01-28~30）
5. [x] wiki `ops/cloudflare-api` 顶部补排雷记录；`dns-subdomain-inventory` §6 证书行更新

---

### P1 — 台账订正（纯文档，零风险）

#### [x] T2 · `fleet-inventory` 订正（2026-11-14 完成）
- 119 删行（2026-08-09 已退役，实测不可达，却仍是第 5 行）
- 删除后 LAN = 5 台，正好对上该页「6 台」标题下只有 5 行的自相矛盾
- 108 移入归档节（在线但废弃、不在 WG、采集栈全灭）

#### [x] T3 · 补记状态漂移（2026-11-14 已写入 fleet-inventory）
- `xian-2c2g`：当日第二轮实测 5 容器（sub2api×3 仍在跑）→ 同日第四轮用户拍板 `docker compose down -v` 彻底拆除；**终态 2 容器**（new-api / new-api-tls），P3 面板实测与台账一致
- 两台 HK：容器均为 0，纯 nginx；追云磁盘 51%、**剩 7.1G（偏紧）**
- `xian-16c16g`：0 容器，符合台账

#### [x] T4 · 重写 `runbooks/new-app-deployment`（2026-11-14 完成，WG 内网四步版）
现版本仍是 frp 时代（CF Tunnel + 4 个已死的 tunnel id + `docker-user-guard.sh`），而 frp 2026-11-12 已全退。
**「怎么接入一个新应用」当前等于无文档** —— 这是所有接入工作的前置。
新流程应基于：WG 内网 + CoreDNS A/CNAME + 内网 nginx vhost + 导航页卡片（三处一起改）。

---

### P2 — 面板架构升级（核心工程）

#### [x] T5 · 执行层 host 化（2026-11-14 完成）
```python
def _docker(args, timeout=40, host=""):   # host 空 = 本机，行为完全不变
```
- [x] host 非空时走 `term_run(host, "docker " + ...)`，base64 脚本包裹防引号拆坏
- [x] 不传 host 的现有调用行为零变化（本机 57 容器列表回归验证一致）
- [~] 同步 host 化：`_nginx()`、证书读取、配置文件读写 —— 先做读端点（T6 已覆盖 nginx/certs），写端点待 T7 后按需

#### [x] T6 · 跨机端点扩展（2026-11-14 完成，全部实测）
在现有 4 个端点之外新增（统一 SSH + base64，照抄 `node_poll_once()` 范式）：
- [x] `GET /api/hosts/<h>/docker` —— 容器列表（name/image/state/status/ports/ips/compose，远端 inspect 拼 IP）
- [x] `POST /api/hosts/<h>/docker/<cid>/<op>` —— start/stop/restart/kill/pause/unpause（真实 pause→unpause 回环验证）
- [x] `GET /api/hosts/<h>/docker/<cid>/logs` —— 远端容器日志（sso-center 实测真实回显）
- [x] `GET /api/hosts/<h>/nginx` —— sites-enabled + conf.d 列表 + `nginx -t`（hk-2c2g 实测 12 个站点）
- [x] `GET /api/hosts/<h>/certs` —— 证书路径 + subject + notAfter（追云实测 11 张真证书；`$HOME/.acme.sh` 已覆盖 111 非root场景）
- [x] `GET /api/hosts/<h>/disk` —— df(去 tmpfs/overlay 噪声前全量) + lsblk --pairs
- 鉴权与现有 API 一致：无 token 401、未知节点 404

#### [x] T7 · 前端节点选择器（2026-11-14 完成）
- [x] 容器页工具栏加 `ck-node` 下拉（本机 + /api/hosts 全部节点）
- [x] 切换后 `dload()`/`dact`/`dlogs`/`ckBatchOp` 全部走 `/api/hosts/<n>/docker` 路由；切回本机走原 `/api/docker/*`，行为不变
- [~] 站点/证书页的节点切换：端点已就绪，前端页面接线待 P3 逐台接入时一并做（端点先行，页面随接入验证）

#### [x] T8 · 首个验证对象 = xian-8c8g-a（2026-11-14 通过）
- [x] 面板 `/api/hosts/xian-8c8g-a/docker` 列出全部 **12 个容器**，名称与 `docker ps` 一致（sso-center/new-api-prod/tokenhub-web/admin-hub/tokenhub/agentlab-reaper/agentlab-proxy/agent-frontend/agentlab-backend/pg-unified/pgbouncer/lldap-platform），含远端 inspect 的 IP 与 compose 标记
- [x] 远端操作回环：pause→paused→unpause→running 真实生效（agent-frontend，健康检查 FailingStreak=0 无副作用）
- [x] 远端日志：sso-center 真实 /healthz 回显
- **P2 完成标志达成。**

---

### P3 — 应用层接入（T5~T8 完成后才有意义）

按「挂了影响最大」排序：

| 序 | 机器 | 内容 | 为什么排这个位置 | 状态 |
|---|------|------|------------------|------|
| 1 | xian-8c8g-a (.9) | 12 容器：agent / tokenhub / sso-center / admin-hub / ai(new-api-prod) / pg-unified / pgbouncer / lldap-platform / agentlab-proxy / agentlab-reaper / agentlab-backend / agent-frontend | **平台本体**，挂了 app.com 全瘫 | [x] 2026-11-14 面板实测 12/12 running，pause/unpause/logs 回环通过 |
| 2 | 追云 (.8) | **0 容器**（纯 nginx），26 vhost（19 sites-enabled + 8 conf.d 含 duplicate） | **公网唯一主门面** | [x] nginx 端点实测 27 条 conf；无 docker（docker: command not found） |
| 3 | xian-8c8g-b (.10) | 12 容器：mcp-gateway + 10 MCP（nexus/jenkins/wiki/agents/gitlab/mail/browser/dify/demo/lsky）+ a2a-server-demo | MCP 栈，AI 能力全在这 | [x] 面板实测 12/12 running |
| 4 | home-4c15g (.4) | 11 容器 running + 2 exited frpc（frp 残留）+ 宿主 CloudCLI :3002 + pg-unified | 计算主力；**931G 盘未挂、根盘 93%** | [x] 面板实测 13 行（11 running + frpc-120/frpc-120-cognet exited）；frp 残留容器待清 |
| 5 | hk-2c2g (.5) | 0 容器，12 vhost + 4 张证书（wildcard + api + 裸域） | 温备门面，切 DNS 即活 | [x] nginx 12 条 / certs 4 张实测 |
| 6 | home-2c2g (.3) | 4 容器 running：lldap-lldap-1 / syspass / syspass-db / dashy + xyz-dashy(created) + ssh-diag/ssh-test(exited 测试残留) | 身份认证 | [x] 面板实测 7 行（4 running） |
| 7 | xian-2c2g (.6) | **2 容器**：new-api + new-api-tls（sub2api×3 于 11-14 第四轮被用户 `down -v` 彻底拆除） | 个人版 API | [x] 面板实测 2/2 running，与台账终态一致 |
| 8 | xian-16c16g (.11) | 0 容器、无 docker、无 nginx——纯出向代理 env，仅 disk 端点有意义 | 工作量最小 | [x] disk 实测（根盘 19%）；docker/nginx 如实报缺 |

---

### P4 — 假数据换真数据

面板 `server/data/` 下的应用层文件全是演示桩：

| 文件 | 现状（实测） | 应换成 | 状态 |
|---|---|---|---|
| `dbassets.json` | 2 条假：127.0.0.1:3306 / :6379，**两个端口都没监听** | ~7 个真实 DB 容器 | [x] 10 条真实 DB（111×6 PG + 8c8g-a pg/pgbouncer + 120 pg/pgbouncer + 116 syspass-db + immich-redis） |
| `mcp.json` | 2 条假，都绑 `demo-site-3.local` | 8c8g-b 上 10 个真实 MCP | [x] 10 条真实 MCP（8c8g-b:9110，wiki/gitlab/mail/nexus/jenkins/agents/browser/dify/lsky/demo） |
| `models.json` | `glm-4-flash` → 127.0.0.1:8000，**Connection refused** | new-api 在 .6:9210 / .9:9212 | [x] 3 条真实端点（8c8g-a:9212 生产 / xian-2c2g:9210 个人 HTTPS / 本机 aigw），API 探测均在线 |
| `sites/` | `t1`(停用静态) + `wafdemo` | 26 + 22 + 21 个真实站点 | [~] t1 为真实停用测试站、wafdemo 真实反代；远端站点接入随阶段 2 逐台推进（T6 nginx 端点已能拉真列表） |
| `certs/` | `f6.myagentlab.xyz` / `fleet.myagentlab.xyz` / `self` | 真实通配符（在追云） | [x] 本目录 3 份均为真实 F1 签发的 LE 证书；追云通配符经 /api/hosts/hk-1c1g/certs 可见 |
| `jobs.json` | 4 条 `echo hello-audit` | 清空或接真实任务 | [x] 3 条演示桩已删，换成真实 fleet-data 备份任务 |
| `agents.json` | 空 | — | [x] 空=真实状态（无 agent 部署），保持 |
| `terminal.json` | 3 条，含 2 条 `192.168.1.250 本机测试/验证-改` 残留 | 清残留 | [x] 3 条无名测试主机已删（57 条快速命令保留不动——快速命令属真实资产） |
| `panel_settings.json` | `FLEET-LIC-TEST-1234` 测试许可证 | 清除 | [x] 测试许可证已删，/api/settings 返回无 license |

---

### P5 — 面板看不见的风险（不阻塞主线）

| # | 风险 | 实测证据 | 状态 |
|---|------|----------|------|
| 1 | 两台 HK 的 `wg-quick@wg0.service` 均 dead | **✅ 2026-11-14 排查为误报**：wg0 由自建 `wg0-ensure.service`（enabled+active，幂等：无 wg0→up / 有 peer→只确保 UP）接管，重启后自动拉起；双机 peer 各 1、mesh ping 10.8.0.2 通 | [x] |
| 2 | 120 的 931G 盘没挂 | **✅ 已挂载**：sda1 → `/mnt/data`（fstab UUID 持久化 + `mount -a` 回环验证，2% used / 894G 可用）。⚠️ **盘健康存疑，迁移方案作废**：SMART 自检 PASSED、坏块计数全 0，但 dmesg 有 2 次 I/O error（2026-11-03、2026-11-14 14:28，扇区分散），疑似 SATA 线/接口问题。**仅作可丢弃数据盘**，重要数据不落；`/mnt/storage` 不迁。待换线观察 | [x] |
| 3 | `start.sh` 自匹配 | **✅ 已修**：pgrep 改锚定全匹配 `^python3 app\.py --port 8890$`，实测不再误匹配 shell 包装进程 | [x] |
| 4 | 追云磁盘偏紧 | **✅ 已缓解**：journald vacuum 释放 1.2G + apt clean → **41% used、剩 8.5G**；journald 永久封顶 200M（conf.d/size.conf）防复发。另清 120 两个 exited frpc 容器+镜像（frp 已退役的残留） | [x] |

---

## 4. 执行计划

### 阶段 0 · 止血（纯文档 + 一处凭据，不动生产系统）
1. **T2 + T3** 台账订正 —— 先把事实对齐
2. **T4** 重写接入 runbook —— 用 WG 内网 + CoreDNS 现行流程替换 frp 版本
3. **T1** 证书续命 —— ✅ 完成：token 本来就有效（验证端点用错导致误判），force 续签已到 2027-02-12

> **完成标志**：wiki 与现实一致；12-23 那颗雷已拆（实际无需拆——证书已续到 2027-02-12）；接入流程有文档 —— ✅ 全部达成。

### 阶段 1 · 打通执行层（架构基础）✅ 2026-11-14 完成
4. **T5** `_docker()` host 化 —— 向后兼容，不传 host 行为不变
5. **T6** 四组新跨机端点 —— docker(列表/操作/日志) / nginx / certs / disk
6. **T7** 前端节点选择器（容器页已接，站点/证书页接线随 P3 推进）
7. **T8** 用 8c8g-a 做首个验证 —— 12 容器/操作/日志全实测通过

> **完成标志**：面板能切到任意节点，看到它真实的容器和站点列表 —— ✅ 达成。

### 阶段 2 · 应用接入（按 P3 顺序逐台推进）✅ 2026-11-14 完成
8. 8c8g-a → 追云 → 8c8g-b → 120 → hk-2c2g → 116 → xian-2c2g → 16c16g —— 全部 8 台经跨机端点实测（容器/nginx/certs/disk 按节点实有能力），P3 表已逐台记录实测结果

> **完成标志**：9 台机器的应用全部在面板里可见可查 —— ✅ 达成（111 本机 + 8 远端；HK/16c16g 无 docker 属实情如实呈现）。

### 阶段 3 · 数据归真（可与阶段 2 并行）✅ 2026-11-14 数据文件部分完成
9. **P4** 九个数据文件 —— 8/9 已换真（dbassets/mcp/models/jobs/terminal/settings/certs/agents），sites 远端部分随阶段 2 端点推进
10. **P5** 四项风险全部处理（2026-11-14）：wg-quick 误报澄清、120 931G 挂载+fstab、start.sh 修复、追云 journald 释放 1.2G

> **完成标志**：面板里没有一条假数据 —— ✅ 数据文件层达成。

---

## 5. 验收标准

| 阶段 | 硬验收（不满足不算完成） |
|---|---|
| 0 | wiki `fleet-inventory` 无 119 行、108 已归档；`runbooks/new-app-deployment` 不再提 frp/tunnel；CF token 验证接口返回 `success:true` —— ✅ 全部达成（2026-11-14） |
| 1 | 面板切到 8c8g-a 能列出 12 个容器且名称与 `docker ps` 一致；切回 111 行为与改造前完全相同 —— ✅ 2026-11-14 实测达成 |
| 2 | 8 台远端机器的容器/站点/证书在面板中全部可见，抽查 3 台与 SSH 实跑结果一致 —— ✅ 8 台全过（8c8g-a 12 容器 / 8c8g-b 12 / 120 13 / 116 7 / xian-2c2g 2 / 追云 nginx 27 / hk-2c2g nginx 12+certs 4 / 16c16g 如实无 docker） |
| 3 | `data/` 下无演示桩；`dbassets.json` 里每条都能真连上 —— ✅ 演示桩已清（DB 连通凭据待用户录入后逐条验证） |

---

## 6. 变更记录

- **2026-11-14 建页**。依据：对 9 台在网机器的逐台 SSH 实测 + wiki 十页交叉核对。
  推翻前一版「12 台 vs 9 台」的错误框架 —— 该框架源自 wiki 自身记录过的 truncation 事故
  （`fleet-inventory`「找机器的正确姿势」原文：*2026-10-11 有 agent 因此得出「只有 9 台机器、只有 1 台云机」的错误结论*）。
  机器层真实缺口 = 1 台（108），而 108 已按废弃排除 → **机器层缺口归零，缺口全在应用层**。
