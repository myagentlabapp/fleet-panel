# fleet-panel 自研自愈闭环

server : flask app  <- 各机 agent 上报 / 面板查询 / 指令下发，SQLite 落盘
agent  : 每台托管机常驻，自检 load/mem/disk/docker + 轮询自愈指令

## 一键起 server
    cd server && python3 app.py --port 8890
    # 页面 http://<IP>:8890  ;  API 见 app.py 头注释

## agent 装到某台机
    python3 agent/agent.py --server http://SERVER_IP:8890 --host <该机名> &
    # 自愈指令: POST /api/hosts/<host>/cmd  {"secret":"FIXME_SERVER_SECRET","proc":"service-restart","cmd":"rsyslog"}

## 阈值 / 通知
app.py 里 THRESH / NOTIFY 改。通知默认打 log，配 FLEET_WEBHOOK 走钉钉/webhook，FLEET_MAIL 走 smtp。

## 安全注意
- 上线换强 token：SERVER 端 FLEET_TOKEN、/api/hosts/<host>/cmd 的 secret
- agent 端 sudo 只放行白名单 service/container 名，不接受任意 shell

## 许可证 (License)

本项目以 **GNU General Public License v3.0 (GPL-3.0)** 发布，全文见根目录 `LICENSE` 文件。

### 借鉴与改编 (Attribution)

fleet-panel 的前端界面与部分功能设计**借鉴 / 改编自 1Panel 社区版** (https://github.com/1Panel-dev/1Panel, GPL-3.0)，
包括：面板布局、容器/站点/证书/终端等页面的交互与 CSS 风格、部分 API 路由与数据结构设计。
1Panel 是 1Panel-dev 的注册商标，本项目与 1Panel-dev 无官方关联。

### 第三方组件 (Third-party components)

本项目打包了若干第三方库，其许可证与本项目不同，按各自许可证条款分发：

- **xterm.js** — MIT License. Copyright © 2019 The xterm.js authors. vendored at `server/static/vendor/xterm/`
- **md-editor (md-editor-v3)** — MIT License. vendored CSS at `server/static/vendor/mdeditor.css`

以上 MIT 组件的版权声明与许可证文本完整保留于 `THIRD_PARTY_NOTICES.md`。
