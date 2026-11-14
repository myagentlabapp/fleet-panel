# fleet-panel 全功能实现 PLAN（对标 1Panel 专业版）

> 状态勾：`[x]` 已实现并跑通 · `[~]` 进行中 · `[ ]` 待做
> 逐段连续交付，每段自带验收，不停下等方向。
>
> **机器/应用纳管另见 [`ONBOARD-PLAN.md`](ONBOARD-PLAN.md)** —— 本文件管「页面对标专业版」，那份管「9 台机器的应用接没接进来」。两者不重叠。

## A. 基础 & 多机（已完成骨架）
- [x] A1 多机总览（server+db+agent 上报，总览表/健康点/失联判定）
- [x] A2 异常告警（阈值判定 + 事件日志 + 通知钩子）
- [x] A3 agent 自愈闭环（指令下发→agent轮询→执行→回报→通知兜底）

## B. 容器管理
- [x] B1 真实接入 Docker API（容器列表：状态/端口/镜像/资源）
- [x] B2 容器操作：启动/停止/重启
- [x] B3 容器日志查看
- [x] B4 镜像列表/拉取/删除
- [x] B5 编排/Compose 管理

## C. 站点 & 应用
- [x] C1 Nginx 站点列表/启停
- [x] C2 一键部署常用应用（通过 Compose 模板）
- [x] C3 反向代理/域名配置

## D. 文件 & 终端
- [x] D1 文件管理器（浏览/上传/编辑/权限）
- [x] D2 Web 终端（浏览器进各机 shell/sudo）

## E. 数据库管理
- [x] E1 连接管理（MySQL/PG/Redis 资产）
- [x] E2 可视化：表浏览/查询/执行
- [x] E3 Redis 键值浏览

## F. SSL & 证书
- [x] F1 证书申请/续期（acme.sh + Cloudflare dns_cf，真实签发 Let's Encrypt；面板内管理、列表、部署到 data/certs）

## G. 计划任务 & 备份
- [x] G1 计划任务（秒级周期调度线程，面板内配置，免 cron.d）
- [x] G2 备份落盘（目录打包为 tar.gz → data/backups，保留列表）

## H. 权限 & 审计
- [x] H1 多用户 + RBAC（admin/operator/viewer；SESS token + X-Fleet-Token 管理员回退）
- [x] H2 审计日志（登录/加用户/改策略/备份等落 events，按 host=audit 区分）

## I. 告警策略 & 插件
- [x] I1 告警策略配置 UI（load/mem/disk/latency 阈值可配）
- [x] I2 通知插件（webhook/钉钉/企业微信/mail，通道启用开关 + 测试按钮）

## 交付规则
- 一段做齐验收（写代码→起服务→真实自测）才标 [x]，不空头打勾。
- 无网络/无权限的项如实标注能力边界，不伪装做完。
- aliyun(10.8.0.7) 恢复为独立支线，有凭据即修，不并入本清单。