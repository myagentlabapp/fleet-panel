# Fleet Panel — 功能对齐目标（先把每个页面功能做到和专业版一样，再谈像素）

> 本文件是**当前唯一的目标清单**。每一步都要对照本文件，不要跑偏。
> 参考底稿：`/tmp/ref-*.html`、`/tmp/ref-*.png`（专业版 2.4.2 已保存的页面与截图）。
> 实现文件：`/home/yy/fleet-panel/server/app.py`（单文件 Flask SPA，约 10779 行）。

## 总则（三条铁律）

1. **功能优先，像素第二。** 页面功能没对齐之前，不做 CSS 微调、不做像素级对齐。
2. **每个页面右侧内容区必须非空白**，且选项卡切换后内容必须变化。
3. **每个交互必须有反应**（弹窗 / toast / 跳转 / 状态变化），不能是死按钮。

## 一、左侧导航（37 项，与专业版完全一致）

参考 `/tmp/ref-概览.html` 中的 `el-menu-item` 与 `el-sub-menu__title`。

专业版顺序（扁平展开）：
概览、应用商店、智能体、模型、AI 网关、Skills Hub、基准测试、MCP、GPU 监控、网站、证书、模板、运行环境、数据库、容器、文件、监控、防火墙、进程管理、SSH 管理、磁盘管理、终端、计划任务、工具箱、APP、WAF、多机管理、用户管理、运维报表、网站监控、资源同步、虚拟机管理、网站防篡改、应用高可用、界面设置、日志审计、面板设置

4 个分组：AI、网站、系统、高级功能。

本地已在 `app.py:6068~6080` 有全部 37 项，需保证：子菜单可展开/收起、激活高亮正确。

## 二、页面功能差距表

### P0 — 本轮必须完成（用户最常用 + 目前最破）

| # | 页面 | view id | 现状 | 要做的事 | 参考文件 |
|---|------|---------|------|----------|----------|
| 1 | 应用商店 | `store` | [x] 5 列卡片网格 / 暗色可用 / 4 tab 切换正常 / 搜索过滤生效 — `/home/yy/fleet-panel/shots/p1-store.png` | 修成 5 列卡片网格；暗色主题可用；4 个 tab 都能正确切换（全部/已安装/可升级/设置）；安装按钮有反应 | `ref-应用商店.html/.png` |
| 2 | 概览 | `overview` | [x] 补 `流量`、`磁盘 IO` 两 tab，实时速率+网卡筛选+echarts 均验证 — `/home/yy/fleet-panel/shots/p1-overview.png` | 补 `流量`、`磁盘 IO` 两个 tab | `ref-概览.html/.png` |
| 3 | 智能体 | `agentstore` | [x] 12 列表格 + 创建弹窗 + 增/改/删/日志/刷新 全流程 API 验证通过 — `/home/yy/fleet-panel/shots/p1-agentstore.png` | 建 view；12 列表格；增删改查按钮 | `ref-智能体.html/.png` |
| 4 | 数据库 | `db` | [x] 4 tab 按类型过滤列表 + 远程服务器/终端/管理▾/搜索/空状态面板 全部实测有反应，增删改查 API 通过 — `/home/yy/fleet-panel/shots/p1-db.png` | 补齐每个 DB 类型的列表内容与「管理/终端/远程服务器」子功能 | `ref-数据库.html/.png` |
| 5 | 容器 | `docker` | [x] 9 tab（概览/容器/编排/镜像/网络/存储卷/仓库/编排模版/配置）逐个切换内容均非空；容器搜索过滤 75→3、总数显示「共 75 条」；启停/日志/镜像拉取/网络/卷/仓库增删 API 全通；模版 tab 已补真实数据行与总条数 — `/home/yy/fleet-panel/shots/p1-docker.png` | 校验每个 tab 内容非空、操作可用（启停/删除/日志） | `ref-容器.html/.png` |
| 6 | 网站 | `sites` | [x] 列表/卡片双模式、类型+分组+搜索过滤、分页与批量选择、创建/设置/启停/删除全链路实测通过；补齐缺失的删除接口、证书过期时间、分组管理（新增/删除/筛选）与备注字段 — `/home/yy/fleet-panel/shots/p1-sites.png` | 校验增删改、证书、WAF 开关 | `ref-网站.html/.png` |
| 7 | 终端 | `term` | [x] 4 tab（终端/主机/快速命令/配置）实测通过：本地与 SSH 主机（111 密钥认证）命令执行真实回显；主机增/改/删/搜索/分组筛选/连接测试✅；分组成立与删除（msgbox 确定）生效；快速命令增/执行/导入/导出；配置字号/行高/字体标签/预览保存与恢复默认均落盘；补齐缺失的 termHostConn 处理函数 — `/home/yy/fleet-panel/shots/p1-term.png` | 校验 xterm 能连上、主机管理可用 | `ref-终端.html/.png` |
| 8 | 计划任务 | `jobs` | [x] 2 tab（计划任务/脚本库）实测通过：创建抽屉（名称/分组/周期/保留份数/备份账号/命令+执行测试）；编辑保存落盘；启用/停用、执行（rc=0 真实回显）、删除；搜索+分组筛选、全选与批量启停/批量删除；分组管理（新增/删除，默认分组保护，任务自动迁回）；执行日志抽屉（列出执行记录、按任务清空）；导入 JSON/导出 jobs.json；脚本库改为真实持久化（data/scripts.json）+ 创建/编辑/执行/克隆/删除/同步 — `/home/yy/fleet-panel/shots/p1-jobs.png` | 校验新建/执行/日志 | `ref-计划任务.html/.png` |

### P1 — 视图容器缺失，需要新建

| # | 页面 | view id | 要做的事 | 参考文件 |
|---|------|---------|----------|----------|
| 9 | 证书 | `certs` | [x] 12 列表格（勾选/ID/域名/其他域名/申请方式/Acme账号/状态/日志/颁发组织/备注/自动续签/过期时间/操作）+ 申请/上传/自签/Acme账户/DNS账户/日志/详情 七个抽屉全部实测；续签预填、部署、单删/批量删（确认框）、自动续签开关落盘、搜索过滤均通过，6 张真实 Let's Encrypt 证书渲染 — `/home/yy/fleet-panel/shots/p1-certs.png` | `ref-证书.html` |
| 10 | 模板 | `tpl` | [x] 模板 tab + 6 列表格（名称/类型/变量定义/备注/时间/操作）+ 创建模板抽屉（名称/类型下拉/变量 textarea/备注）落盘、搜索过滤、生成产物抽屉（选模板/产物名/变量值）→ 产物列表抽屉（真实 `/api/col/tplart` 持久化，可再生成/删除）、删除带确认框 均实测通过 — `/home/yy/fleet-panel/shots/p1-tpl.png` | `ref-模板.html` |
| 11 | 运行环境 | `env` | [x] 6 个 tab（PHP/Java/Node.js/Go/Python/.NET，与参考顺序一致）+ 11 列表格；创建抽屉（名称/类型/目录/来源/版本/镜像/端口/备注）按类型落盘、6 个 tab 切换分别过滤显示、搜索+重置、启动/停止切换状态、日志抽屉、删除确认框、扩展模版抽屉（从模板生成环境）、清理构建缓存（确认框+真实 `/api/toolbox/clean`）、刷新间隔下拉 均实测通过 — `/home/yy/fleet-panel/shots/p1-env.png` | `ref-运行环境.html` |
| 12 | 监控 | `mon` | [x] 3 tab（监控/导出/设置）+ 时间范围工具栏（今天/昨天/近3天/近7天/近30天/清空/确定）+ 平均负载/CPU/内存/磁盘 I/O/网络 五张图（真实 /proc 后台采样落盘，磁盘设备与网卡下拉，所有=合计收发）+ 导出 CSV（下载/预览前30行）+ 监控设置（采集间隔/保留天数落盘 `/api/mon/settings`）均实测通过 — `/home/yy/fleet-panel/shots/p1-mon.png` | `ref-监控.html` |
| 13 | 进程管理 | `proc` | [x] 2 tab（进程/网络）实测切换：进程表 11 列（PID▲/名称/父进程ID/线程/用户/CPU/内存/连接/状态/启动时间/操作）共 683 条真实数据；状态下拉 7 项（运行中/睡眠/停止/空闲/等待/锁定/僵尸进程）+全部，与参考完全一致；PID/名称/用户 三过滤联动（睡眠→604、nginx→110）；PID/CPU/内存 排序（▲/▼ 实测 0.00%→24.40%）；查看详情抽屉显示真实 cmdline（新增 `/api/proc/detail`）；结束进程；网络 tab 5 列（协议/本地地址/远程地址/状态/进程名+pid）共 982/1083 条 — `/home/yy/fleet-panel/shots/p1-proc.png` | `ref-进程管理.html` |
| 14 | 磁盘管理 | `disk` | [x] 按物理盘分卡实测 3 卡（sda 系统盘 / sdb / sdc）：卡头 `磁盘名称` + `系统磁盘` 标签 + 大小/分区/磁盘类型(SSD·HDD)/设备型号/序列号；每卡 8 列表格（分区名称/大小/已用/可用/使用率/挂载目录/文件系统/操作）实测行 sda1 1G 6.1M 1G 1% /boot/efi vfat 无法操作、sda3 116.2G 30.2G 78.6G 28% / ext4 无法操作、sdb 3.6T 2.2T 1.2T 65% /mnt/data ext4 卸载；系统盘底部提示「提示：当前磁盘为系统盘，无法进行操作」；挂载/卸载 API 用 loop 设备真实验证（挂载成功→findmnt 可见→卸载成功），新增 `/api/disk/mount`、`/api/disk/umount`，使用率改用 df 口径 — `/home/yy/fleet-panel/shots/p1-disk.png` | `ref-磁盘管理.html` |
| 15 | 资源同步 | `sync` | [x] 4 tab（文件对传/镜像对传/应用对传/证书同步，与参考顺序一致）+ 企业版到期提醒（快速跳转）+ 双栏：左栏真实目录浏览（`/api/sync/fs`，本机 os.listdir / 远端 SSH ls，/home/yy 95 条真实条目，进入/选择）+ 右栏同步任务（`/api/col/sync` 创建抽屉/日志抽屉/删除）+ 节点下拉来自 `/api/sync/nodes`（home-4c31g）；三个 tab 空态自动列出可对传对象（镜像 15 / 应用 12 / 证书 6）；新增 `/api/sync/fs`、`/api/sync/run`（真实 rsync/scp/docker save-load，实测 TARGETS.md→/tmp/sy-test rc=0 落盘成功） — `/home/yy/fleet-panel/shots/p1-sync.png` | `ref-资源同步.html` |
| 16 | 网站防篡改 | `tamper` | [x] 复刻参考版空态（`未检测到 OpenResty ，请进入应用商店点击安装！` + `去应用商店安装` 点击跳转 store，实测 store 内容非空）+ 真实 7 列表格（名称/类型/防护目录/状态/总防护/今日防护/操作）由 `/api/tamper/sites` 驱动 14 个真实站点、总防护/今日防护按模板与保护状态真实统计；保护↔取消保护落盘 site.json 并写审计（实测未保护→保护中）；新增「防护模版」第二表格 + `保护模版/排除模版/不刷新` 三个抽屉真实落盘 `data/tamper.json`（`/api/tamper/tpl` 新增/删除，删除带确认框），实测新增→列表 3 行→删除→2 行，空时间回填 `-`；替换原先假 DOM 插行与只 toast 的两个死交互 — `/home/yy/fleet-panel/shots/p1-tamper.png` | `ref-网站防篡改.html` |
| 17 | MCP | `mcp` | [x] 单 tab `router_card`（MCP）+ 创建/绑定网站/刷新工具栏；6 列表格（名称/外部连接地址/状态/日志/时间/操作）由 `/api/col/mcp` 驱动，`el-tag` 状态徽章；创建抽屉（名称/外部连接地址/日志）落盘 `status=未连接`；配置抽屉（改名/URL/日志/测试连接）实测 未连接→已连接 并追加日志（新增 `/api/mcp/test` 真实 socket+HTTP 探测）；日志抽屉；绑定网站抽屉从 `/api/sites` 取 14 个站点并落盘 `binds`；`fpConfirm` 删除；刷新 toast 均实测 — `/home/yy/fleet-panel/shots/p1-mcp.png` | `ref-MCP.html` |
| 18 | 基准测试 | `bench` | [x] 单 tab `router_card`（基准测试）+ 企业版到期提醒（快速跳转）+ 创建/刷新工具栏；9 列表格（名称/模型/上下文长度/输出吞吐/总吞吐/首 Token 延迟/状态/时间/操作）由 `/api/bench` 驱动（真实落盘 `data/bench.json`），`el-tag` 状态徽章；创建抽屉（名称/模型/上下文长度）→ `/api/bench/start` 后台 15s 生成指标并写日志，实测 运行中→已完成；详情抽屉展示全部指标+执行日志（替代 alert 死桩）；删除走 `fpConfirm` + `/api/bench/<name>/rm`（实测 2 条→1 条）；刷新 toast；分页「共 N 条」联动 — `/home/yy/fleet-panel/shots/p1-bench.png` | `ref-基准测试.html` |
| 19 | APP | `app` | [x] 单 tab `router_card`（APP）+ 企业版到期提醒（快速跳转）+ 信息提示条；绑定 Key 下拉（只列 `data/apikey.json` 中 status=有效 且 开启扫码 的 Key）+ 创建 API Key / 管理 API Key / 刷新 三个按钮；面板别名（落盘 `data/app_cfg.json`）/ 暂无可扫码绑定 Key 提示 / 显示二维码（新增 `/api/app/qr` 返回真实 SVG 二维码，`fleetapp://bind` 深链载荷，未绑定前禁用）+ 多设备共用提示。实测：创建 my-phone → 开启扫码绑定 → 绑定成功（写 bindings）→ 二维码抽屉渲染出二维码 → 别名保存为「家庭面板」→ 刷新后状态回填全部通过 — `/home/yy/fleet-panel/shots/p1-app.png` | `ref-APP.html` |

> 注：`agentstore` 在 view 列表里出现过，但 `show('agentstore')` 跳转后是否真有内容需实测。

### P2 — 已有 view，但 tab/字段不全

| # | 页面 | view id | 缺什么 | 参考文件 |
|---|------|---------|--------|----------|
| 20 | 面板设置 | `cfg` | [x] 8 个 tab 全部真实落地（面板/安全/告警通知/备份账号/快照/许可证/API Key/关于，逐个切换内容非空，备份账号 1 行、快照 3 行、API Key 2 行、关于 8 行）；面板 tab 复刻参考版 10 行表单（主题颜色 亮色/暗色/跟随系统 三选一 + 自定义取色、菜单标签页 启用/停用、水印设置 启用/停用、面板别名、系统语言 12 种、面板超时时间、默认访问地址、代理服务器、菜单设置、运行环境），点击均有反应并落盘 `data/panel_settings.json`；新增主题引擎 `setTheme/_applyTheme/setThemeCustom`（暗色实测 body 背景 rgb(30,30,30)、auto 跟随 matchMedia、主色可改）；新增 `/api/settings`、`/api/settings/backupacct`、`/api/panel/snapshots`（真实 tar.gz 1.1MB，可下载/删除）、`/api/about`；菜单设置勾选 37 项即时隐藏/恢复侧边栏；告警通知保存与测试通知改成 fpToast（去掉 alert 死桩） — `/home/yy/fleet-panel/shots/p1-cfg.png` | `ref-面板设置.html` |
| 21 | 界面设置 | `uiset` | [x] 单 tab `界面设置` + Logo(带文字/不带文字/网站图标) / 登录页(图片/背景类型 图片·背景色/背景图片/背景色/按钮链接颜色) / 底部导航(4 条链接：勾选+128 字计数) 三段表单，恢复默认(确认框+`/api/uiset/reset`)/重置/保存(脏标记启用) 全部实测；5 张图片上传→预览→落盘 `data/ui.json`→刷新回填，并实时应用到侧边栏大/小 Logo、`<link rel=icon>`、登录页图片与背景；暗色主题实测 body rgb(30,30,30) — `/home/yy/fleet-panel/shots/p1-uiset.png` | `ref-界面设置.html` |
| 22 | 多机管理 | `nodes` | [x] 三个 radio tab（概览/节点管理/面板管理）真正切换内容；企业版到期提醒 + 快速跳转 + 关闭；多机管理卡补 分组下拉/搜索/刷新/分页（共 1 条 · 20条/页）；六个统计卡各自 ⟳ 刷新并挂真实子表：应用←`/api/overview`、网站←`/api/sites`(14)、数据库←`/api/db/assets`、计划任务←`/api/jobs`(4)、证书←`/api/certs`(6)、智能体←`/api/agents`(回退 quicks.agent)；**TARGETS 缺的两列已补**：数据库卡改 4 列表格 名称/已授权用户/描述/操作，含类型下拉(全部/MySQL/MariaDB/PostgreSQL/MongoDB/Redis)+节点下拉+搜索+「暂无数据」空态+「共 N 条」，实测 2 行→类型 mysql 过滤 1 行→搜索无结果出空态→还原 2 行，详情抽屉显示类型/地址/授权用户/连接状态/描述；节点管理(1 行)/面板管理(1 行) 两页表格有表头有数据，添加节点抽屉展示真实主节点地址与接入 Token（删除原先伪造的 install.sh 接口），同步面板配置走 fpConfirm — `/home/yy/fleet-panel/shots/p1-nodes.png` | `ref-多机管理.html` |
| 23 | 用户管理 | `users` | [x] 数据行补全（admin 行含 本地/超级管理员/描述）；创建/编辑/删除/批量删除全走 fpDrawer+fpConfirm 并对接 `/api/users`、`/api/users/<n>/role`、`/api/users/<n>/rm`、`/api/users/rm`；三个 tab（用户/角色/认证管理）切换内容均变化，认证管理内 AD/LDAP·OIDC·SAML2 三 provider 面板与 基础配置/定时同步/同步记录 三竖 tab 均切换；认证配置落盘 `data/users_auth.json`，测试连接/测试登录/用户导入走真实 ldap3 探测（连接被拒错误真实回显并写入同步记录 Failed 行）；内置角色与 admin 删除有保护提示；暗色主题正常 — `/home/yy/fleet-panel/shots/p1-users.png` | `ref-用户管理.html` |
| 24 | 日志审计 | `audit` | [x] 4 个子 tab（操作/访问/系统/任务）全部真实切换：colgroup+thead 随 tab 变化，tbody 走真实接口 —— 操作 `/api/audit`（共 1574 条）、访问 `/api/loginlog`、系统 `/api/logs?type=system`（journald 真实行，服务下拉 8 个服务、优先级 0-7、关键字过滤实测 kw=kernel 得 5 行）、任务 `/api/logs?type=task`（`data/joblog.json` 200 条）；筛选控件按 tab 显隐（资源/节点 仅操作，服务/优先级 仅系统，状态 除系统外）；清空日志按子 tab 映射 logType（access/sshlog/login→login、sys→system、task→task）并带确认框；4 个 pane（面板日志/主机日志/登录日志/网站日志）切换内容非空，定时刷新与分页均按当前子 tab 生效 — `/home/yy/fleet-panel/shots/p1-audit.png` | `ref-日志审计.html` |
| 25 | 文件 | `files` | [x] 真实 8 列表格（名称/权限/用户·用户组/大小/修改时间/备注/操作）共 96 行、面包屑+⌂+根目录跳转；创建/上传下载/文件工具 三个菜单、每行「更多」与右键菜单；全选与批量 复制·移动·压缩·权限·删除；搜索与子目录递归搜索；编辑抽屉；回收站还原/彻底删除/清空；收藏夹；计算目录大小；上传/下载；修复 `fj()` 未转义导致还原链接 onclick 截断的 bug — `/home/yy/fleet-panel/shots/p1-files.png` | `ref-文件.html` |
| 26 | WAF | `waf` | [x] 7 个 tab（概览/攻击报表/拦截记录/封锁记录/黑白名单/网站设置/全局设置）逐个实测内容非空且切换变化；概览 4 张真实统计卡（请求数来自 nginx 日志）；攻击报表 4 个子筛选（攻击统计/接口攻击/DDOS/CC）+ 5 列表格；拦截记录 5 列（/api/waf/records）；封锁记录 5 列 + 解除封锁（新增 ignore 落盘，实测解除后行消失）；黑白名单 5 列 + 添加黑/白名单抽屉 + 移除（新增面板名单 `data/waf.json`，nginx allow/deny 只读展示，实测添加→2 行→移除→1 行）；网站设置按站点真实启停（写 site.json `waf` 字段，未单独设置显示「继承全局」，实测 已防护→关闭→未防护）；全局设置 4 项防护开关 + 全局开关全部落盘（实测文件 enabled/sqii/xss/crawler/cc 变化）；修复后端 `/api/waf/lists` 的 `w=sh` 别名与 `(w or sh)` 丢黑名单 bug；亮/暗色实测正常 — `/home/yy/fleet-panel/shots/p1-waf.png` | `ref-WAF.html` |
| 27 | 网站监控 | `wmon` | [x] 5 个 tab（概览/访问统计/趋势统计/请求日志/网站列表）逐个实测内容非空且切换变化；概览 8 项指标来自真实 nginx 日志解析（浏览量/访客/独立 IP/流量/蜘蛛/请求数/4xx/5xx），未开启提示条随 `/api/wmon/status` 自动显隐、立即开启走 fpToast；访问统计 3 张聚合表（热门路径/独立 IP/状态码分布，含占比与类别）；趋势统计 echarts 折线图 + 按小时/按天切换均改变表格；请求日志 7 列表格 + 状态码下拉过滤（2xx/4xx 实测）+ 关键字搜索（index→6 条）+ 共 N 条；网站列表 14 站点 + 监控总开关 + 查看日志跳转；新增 `_wmon_rows()` 日志解析与 `/api/wmon/stats`、`/api/wmon/logs` — `/home/yy/fleet-panel/shots/p1-wmon.png` | `ref-网站监控.html` |
| 28 | 运维报表 | `report` | [x] 9 个 tab（概览/主机运行/登录与安全配置/网站防护/运行资源/计划任务/告警通知/导出历史/设置，与参考顺序一致）逐个实测内容非空且切换变化：概览 服务器安全运营概览评分 + 5 个统计卡（可点击跳转对应 tab）+ 5 张资产卡（真实计数 + 查看链接）+ 风险项 4 列表格 + 评分趋势 echarts；主机运行 12 项 KV（真实 hostname/内核/负载/内存/磁盘）+ CPU·内存 双折线图 + 采样记录表；登录与安全配置/网站防护/运行资源/计划任务/告警通知 均为真实接口驱动的多列表格（登录日志、证书到期、容器状态、cron 日志、告警渠道）；导出历史 已生成 N 份报表 + 导出 + 操作日志；设置 4 项（默认天数/中风险阈值/高风险阈值/采集保留天数）落盘 `data/report_settings.json` 并同步 `mon_settings.json`；工具栏 刷新/导出/报表节点下拉/时间范围 7·30·90 天均实测，导出真实生成 CSV 并写 `data/report_exports.json` + 操作日志；鉴权实测 GET 无 token 401、POST 导出无 token 403；新增 `/api/ops/report`、`/api/ops/report/export`、`/api/ops/report/settings` — `/home/yy/fleet-panel/shots/p1-report.png` | `ref-运维报表.html` |
| 29 | 虚拟机管理 | `kvm` | [x] 6 tab（概览/虚拟机/镜像/模板/网络/存储池，与参考顺序一致）逐个实测非空且切换变化：概览 2426 字符（许可证提示条+`1Panel-kvm` 标签+依赖链接+hero 含已禁用的「孤立数据清理」+4 统计卡+资源概况 3 行进度+风险提醒+存储池概况表格）；虚拟机 478 字符/4 表头/共 0 条；镜像 613/4；模板 493/6；网络 397/4；存储池 399/4（空态为正确 fallback）。存储池全链路真实可用：通过 UI 新增→`pool-define-as`→`pool-start`→`pool-destroy`→`pool-undefine` 全部实测通过；镜像上传→列表→删除实测；依赖抽屉展示真实 CPU 硬件虚拟化 不支持 / /dev/kvm 未挂载 / libvirt 已安装 / 连接状态 已连接 / QEMU 未安装；鉴权 GET 无 token 401、POST 无 token 403；**本机无 `/dev/kvm`、无 vmx/svm、未装 qemu-system-x86_64，故虚拟机与网络启动按真实 virsh 报错降级展示（不伪造成功）**；新增 `/api/kvm`、`/api/kvm/pool`、`/api/kvm/net`、`/api/kvm/image`、`/api/kvm/image/upload`、`/api/kvm/vm` — `/home/yy/fleet-panel/shots/p1-kvm.png` | `ref-虚拟机管理.html` |
| 30 | 应用高可用 | `ha` | [x] 3 个 radio tab（MySQL/PostgreSQL/Redis，顺序与参考一致）逐个实测内容非空且切换变化：MySQL = 7 列集群表（集群名称/类型/节点/可用节点/状态/创建时间/操作）+ 4 列「已安装的 MySQL 实例」表；PostgreSQL = 空态「尚未安装任何应用」+ 前往数据库（实测跳转 db）；Redis = 信息提示条 + 已安装实例表；标题随 tab 变为「X 集群」；企业版到期提醒条 快速跳转→cfg、✕ 关闭均实测；添加集群抽屉（集群类型/节点勾选/集群名称）实测校验「请填写集群名称」「请至少选择一个节点」，成功后落盘 `data/ha.json` 并写审计；详情抽屉（节点逐条状态表）/检测（真实 TCP 探测，回显 x / y 可用）/删除（fpConfirm 确认框）全部实测；节点状态来自真实 TCP 探测，3306/6379/5432 本机均关闭故如实显示 未连接 / 异常，不伪造；鉴权 GET 无 token 401、POST 无 token 403；新增 `/api/ha` — `/home/yy/fleet-panel/shots/p1-ha.png` | `ref-应用高可用.html` |
| 31 | AI 网关 | `aigw` | [x] 9 个 tab（概览/账号池/模型组/API Key/用户组/智能路由/内容合规/用量统计/设置）全部由真实 `/api/aigw` 驱动、逐个切换内容非空；概览 echarts 使用趋势+5s 刷新；账号池（导入模型/新增/编辑/测试/启停/删除，真实 TCP 探测如实显示 异常）、模型组、API Key（fpPrompt+删除）、用户组（Default 编辑落盘 30）、智能路由（规则预览+样本增删）、内容合规（敏感词增删）、用量统计（分布/排行榜/调用日志/详情抽屉，全部读 `data/aigw_usage.json` 真实记录）、设置（8 组表单保存落盘 `data/aigw.json` + Embedding 真实连通测试）均实测通过；启停网关后代理真实返回 503；真实调用 `/aigw/v1/chat/completions` 按 Bearer Key 归属用户并写入用量（`{"model":"glm-4-flash","status":200,"tokens":24,"user":"my-phone"}`）；鉴权 GET 无 token 401、POST 无 token 403 — `/home/yy/fleet-panel/shots/p1-aigw.png` | `ref-AI_网关.html` |
| 32 | 模型 | `models` | [x] 2 tab（模型账号/本地模型）逐个实测切换：模型账号 8 列表格由 `/api/col/models` 驱动、`glm-4-flash` 行含真实 `验证失败` el-tag（title 为真实 `连接失败: <urlopen error [Errno 111] Connection refused>`）与 验证/编辑/删除；API 类型下拉 9 项（与参考一致）+ `anthropic-messages` 过滤得 暂无数据 + 搜索 glm/zzzz 命中与空态；本地模型切 tab 后隐藏筛选栏、表头变 6 列并如实显示「未检测到本地推理服务（ollama / vllm）…」共 0 条；创建抽屉「获取模型」真实请求 `/api/models/probe`，对 `http://127.0.0.1:8890/aigw/v1` 返回真实 2 个模型 auto/glm-4-flash；新增 `POST /api/models/probe`、`POST /api/models/verify`（真实探测并落盘 verified/verify_msg/verify_time/pool），鉴权 POST 无 token 403 — `/home/yy/fleet-panel/shots/p1-models.png` | `ref-模型.html` |
| 33 | GPU 监控 | `gpu` | [x] 2 个 radio tab（实时监控/历史记录）由 `gpuTab()` 真正切换：实时监控显示真实 `/api/gpu` 探测结果（本机无 nvidia-smi / rocm-smi，故如实显示「当前系统未检测到支持的 GPU/XPU/NPU 管理指令，请检查后重试！」+ no_app.svg，不伪造）；历史记录 6 列表格（时间/GPU/温度/使用率/显存/Bus ID）+ 共 N 条 + 「暂无历史记录：本机未检测到支持的 GPU/XPU/NPU，实时探测有数据后会自动采样」空态（有数据时按 200 条倒序渲染，已用桩数据实测 2 行正确回填）；标题随 tab 变为「GPU 历史记录」；右上 刷新 按钮按当前 tab 分别重载并弹 fpToast「已刷新」；新增 `GET /api/gpu/hist`（读 `data/gpu_hist.json`，实时探测有设备时自动采样，保留 5000 条），鉴权 GET 无 token 401 — `/home/yy/fleet-panel/shots/p1-gpu.png` | `ref-GPU_监控.html` |
| 34 | 防火墙 | `firewall` | [x] **参考页实为 4 个 radio tab（主机防火墙/容器端口防护/端口转发/设置），文档原写「6 tab」有误，按参考页 4 个对齐**；逐个实测非空且切换变化：主机防火墙 80 条/表头 `动作 优先级 协议 IP 端口 已使用 描述 操作`/状态卡 已停止 + 提示「当前未开启系统防火墙，请先开启！」；容器端口防护 107 条/表头 `动作 协议 绑定地址 端口映射 容器 状态 描述 操作`/首行 `容器 TCP 127.0.0.1 9212->3000 new-api 已映射` + 详情抽屉；端口转发 0 条（空态）；设置 tab 隐藏工具栏/分页并显示 默认入站/出站策略、日志级别 off/low/medium/high、IPv4 转发、保存/刷新。写入类按钮**全部返回真实错误、不伪造成功**：开启→`系统未安装 ufw/iptables, 无法开启防火墙`；重启→`系统未启用防火墙`；重置→`系统未安装 ufw`；创建(主机)→`系统未启用防火墙(无 ufw/iptables), 规则未创建`；创建(转发)→`系统未安装 iptables, 无法创建 DNAT 转发规则`；编辑提交→`系统未安装 iptables, 无法修改规则`；删除→`删除完成 0 条，失败 1 条：端口转发由容器/服务实际监听端口承载…`。选择 20 条后 `#fw-del-btn` 由 `fw-b dis` 变可点；导出实测下载 `firewall-export.txt`；导入回读 18 字符成功；搜索 80→6→80；分页 1→2→3 + 前往 4 → 回 1（行内容随页变化）；不刷新/5 秒/非法值三态实测（定时器 true/false/错误 toast）；设置保存两次实测落盘 `server/data/firewall.json`（log=medium、forward=true）；鉴权 GET 无 token 401、POST 无 token 403（`/api/firewall/cmd` 例外：返回 200 + `{"ok":false,"error":"无写入权限"}`，状态码不一致但非绕过，如实记录）；新增 `POST /api/firewall/settings` — `/home/yy/fleet-panel/shots/p1-firewall.png` | `ref-防火墙.html` |
| 35 | SSH 管理 | `ssh` | [x] 3 tab（配置/会话/登录日志）实测切换非空：基础配置 6 行（连接端口/监听地址/root 用户/密码认证/密钥认证/反向解析）+ 每行「设置」按钮 + 开关；**六项显示值改为以 `sshd -T` 生效配置为准**（原来只解析主文件，忽略 `Include /etc/ssh/sshd_config.d/*.conf` 的 drop-in，导致 root/dns/listen 三项报错），实测与 `sudo sshd -T` 完全一致：port `22, 23030`、listen `192.168.1.111, 10.8.0.1, 10.8.0.2`、root `yes`→「允许」、pwd `no`→关、key `yes`→开、dns `no`→关；监听地址已去重并剥掉 `:端口`（`sshd -T` 输出的是地址×端口笛卡尔积）；条件覆盖表 4 条真实 Match 行（Address 10.8.0.0/16、fdcc:…::/64、192.168.1.0/24、User yangyong，均 PasswordAuthentication yes）；全部配置表 20 行=文件真实 20 条有效指令，表头 行号/指令/取值/操作，首行 `12 Include /etc/ssh/sshd_config.d/*.conf`；会话 3 条真实登录（yy [session-01]·[session-02]· [session-03][client-ip]）+ 强制下线；登录日志 20 条真实记录（登录 IP/归属地/端口/登录方式/用户/登录状态/时间）+ 清空/导出/成功·失败筛选/不刷新·5s–300s 定时 + 分页；密钥信息抽屉 3 个真实主机密钥（ [host-key-01]/  [host-key-02]/  [host-key-03]+ SHA256 指纹 + `sshd -t 校验：通过`）；授权密钥抽屉 4 条真实 [authorized-keys]（ [key-01]/  [key-02]/  [key-03]/ [key-04]）+ 删除 — `/home/yy/fleet-panel/shots/p1-ssh.png` | `ref-SSH_管理.html` |
| 36 | 工具箱 | `toolbox` | [x] 6 tab（快速设置/缓存清理/进程守护/病毒扫描/FTP/Fail2ban，与参考顺序一致）逐个实测内容非空且互不相同（66/267/36/32/44/107 字符）：快速设置 8 行真实值（DNS `114.114.114.114 8.8.8.8 …`、Hosts、Swap `/swap.img`、主机名 `home-4c31g`、系统密码 `******`、NTP `ntp.ubuntu.com (默认)`、时区 `Asia/Shanghai`、实时服务器时间）+ 每行「设置/同步」；7 个设置抽屉（Swap/密码修改/系统时区/NTP 服务器/DNS 测试可用性/主机名/Hosts）全部渲染非空，时区提交真实落盘并回显「已设置时区: Asia/Shanghai」，服务器时间同步走真实 `timedatectl`，DNS 测试真实解析 `www.baidu.com → 153.3.238.127`（多值 DNS 只测主服务器并注明共 4 个）；缓存清理 6 类垃圾分类统计 + 真实删除实测「已清理 2 个文件，释放 12 B」（/var/tmp 两个测试文件事后确认已消失）；进程守护/病毒扫描/FTP 未安装时如实提示「未检测到 …，请前往脚本库页面手动安装！」+ 快速跳转（不伪造运行中）；Fail2ban 真实 `systemctl is-active` = 运行中 + 真实启动/重启按钮；**修复 `/api/toolbox/services` 把容器内 supervisord 进程误判为本机服务的问题**（改为二进制存在才算 present）；**修复 `/api/toolbox/restart` 自杀 bug**（pkill 模式命中面板自身 cmdline，改为 detached `setsid bash -c 'sleep 1; pkill …; exec bash /tmp/start-panel.sh'`），实测重启后 pid 变化且 `面板已重启完成`；重启服务器按钮只弹确认框后取消，未执行（安全），并以 `sudo -n shutdown -c` 兜底；面板以非 root 用户 `yy` + 免密 `sudo -n` 运行 — `/home/yy/fleet-panel/shots/p1-toolbox.png` | `ref-工具箱.html` |
| 37 | Skills Hub | `skills` | [x] 单 tab `router_card`（Skills Hub）+ 企业版到期提醒（温馨提醒 `[5] 天后到期`，快速跳转→`cfg`、✕ 关闭均实测）+ 上传 Skill / 导入 Skill / 智能体 Skill 目录 / 刷新 四按钮；8 列表格（名称/描述/版本/来源/状态/风险等级/更新时间/操作）由 `/api/skills` 驱动 27 条真实扫描 Skill（读 `~/.claude` 下真实 SKILL.md，落盘 `data/skills.json`），分页「共 27 条 10条/页 1 前往 1 页」；搜索 playground→1 条 / zzzzz→暂无数据 / 清空→27 条；状态筛选抽屉（全部/已启用/未启用）实时过滤；详情抽屉显示名称/描述/版本/来源/状态/风险等级/文件路径/更新时间 + 安全检查按钮（真实 8 条正则扫描，playground 扫 7 个文件→风险 低/未发现风险项）；上传 Skill 抽屉（名称/描述/版本/内容，校验「请填写 Skill 名称」「请粘贴 SKILL.md 内容」）实测新增 browser-demo→扫描出 `风险 高 … 危险删除命令 SKILL.md:9 rm -rf /tmp/x`；导入 Skill 抽屉（路径模式对已存在 Skill 如实报 `成功 0 个，失败 1 个：…同名 Skill 已存在: playground`，JSON 非法如实报 `JSON 解析失败`，合法 JSON 新增 json-demo 来源=自定义）；智能体 Skill 目录抽屉（`GET /api/skills/agentdir` 显示 `~/.claude/skills`，安装 browser-demo→落盘可见，fpConfirm 移除→已移除）；启用/停用、删除（fpConfirm 确定删除、取消不变）全部实测；新增 `/api/skills`、`/api/skills/<n>/toggle`、`/api/skills/install`、`/api/skills/<n>/rm`、`/api/skills/<n>/scan`、`/api/skills/agentdir`、`/api/skills/agentdir/install`、`/api/skills/agentdir/rm`；鉴权 GET 无 token 401、POST 无 token 403；亮/暗色实测正常（暗色 body rgb(30,30,30)、面板 rgb(43,43,43)）；测试数据已清理（删除 browser-demo 及其 skillfiles 目录、rmdir `~/.claude/skills`、json-demo 已删），最终 27 条真实数据 — `/home/yy/fleet-panel/shots/p1-skills.png` | `ref-Skills_Hub.html` |

## 三、验收标准（逐页打勾，别跳）

每个页面必须同时满足：

- [ ] 点侧边栏能进入，右侧 `.content` **非空白**
- [ ] 每个 tab 切换后内容**确实变化**
- [ ] 页面上每个按钮/链接点击**有反应**
- [ ] 表格有表头 + 至少 1 行示例或真实数据
- [ ] 亮色/暗色切换后该页正常
- [ ] 与 `/tmp/ref-<页名>.png` 并排比，**结构**（不是像素）一致

## 四、执行顺序（本轮）

1. `store` 应用商店（卡片网格 + 暗色） → 2. `overview` 补 2 tab → 3. `agentstore` 建 view → 4. `db` 校验 → 5. `docker` 校验 → 6. `sites` 校验 → 7. `term` 校验 → 8. `jobs` 校验 → 9~19 P1 建 view → 20~37 P2 校验。

每完成一页，在本文件对应行打 `[x]`，并记下截图路径。

## 五、禁忌

- 功能没补齐前，禁止做像素级 CSS 微调。
- 禁止新增与专业版无关的页面或 API。
- 禁止改动已验证的 API 签名（`/api/app-templates` 等）。
- 每次改动后必须重启 8890 并重新截图验证，不能凭感觉说「好了」。